#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastBlog 发布构建脚本
支持 Astro 前端，自动从 Git 提交生成发布说明（含多行 body）
精简版 —— 适配 frontend-astro
"""

import argparse
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 项目根目录
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


# ---------- 版本信息工具 ----------
def get_current_version() -> str:
    """获取当前版本号"""
    try:
        from shared.utils.version_manager import version_manager
        return version_manager.get_backend_version().get("version", "1.0.0")
    except Exception:
        return Path("version.txt").read_text(encoding="utf-8").strip()


def get_backend_versions() -> List[str]:
    """后端 Python 依赖版本"""
    versions = [f"- Python: {platform.python_version()}"]
    try:
        requirements = Path("requirements.txt").read_text(encoding="utf-8").splitlines()
        important = [
            "fastapi", "uvicorn", "sqlalchemy", "pydantic",
            "alembic", "passlib", "python-jose", "python-multipart",
            "pillow", "requests", "aiofiles"
        ]
        found = {}
        for line in requirements:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            for pkg in important:
                if line.lower().startswith(pkg):
                    if "==" in line:
                        name, ver = line.split("==", 1)
                    elif ">=" in line:
                        name, ver = line.split(">=", 1);
                        ver = f">={ver}"
                    elif "<" in line:
                        name, ver = line.split("<", 1);
                        ver = f"<{ver}"
                    else:
                        name, ver = line, "latest"
                    found[name.strip()] = ver.strip()
        for pkg in sorted(found):
            versions.append(f"- {pkg}: {found[pkg]}")
    except Exception:
        versions.append("- 无法读取 requirements.txt")
    return versions


def get_frontend_versions() -> List[str]:
    """前端 Astro 依赖版本"""
    versions = []
    pkg_path = project_root / "frontend-astro" / "package.json"
    if not pkg_path.exists():
        return ["- 无法读取 frontend-astro/package.json"]
    try:
        data = json.loads(pkg_path.read_text(encoding="utf-8"))
        deps = data.get("dependencies", {})
        dev_deps = data.get("devDependencies", {})
        all_deps = {**deps, **dev_deps}

        # 核心框架
        for pkg in ["astro", "react", "react-dom", "@astrojs/react"]:
            ver = all_deps.get(pkg)
            if ver:
                versions.append(f"- {pkg}: {ver}")

        # 样式/工具
        for pkg in ["tailwindcss", "postcss", "autoprefixer", "typescript"]:
            ver = all_deps.get(pkg)
            if ver:
                versions.append(f"- {pkg}: {ver}")
    except Exception:
        versions.append("- package.json 格式错误")
    return versions if versions else ["- 无依赖信息"]


def format_version_list(versions: List[str]) -> str:
    return "\n".join(versions) if versions else "- 暂无版本信息"


# ---------- 发布构建器 ----------
class ReleaseBuilder:
    def __init__(self, version: str, output_dir: str = "release"):
        self.version = version
        self.output_dir = Path(output_dir)
        self.project_root = project_root
        self.build_temp = Path(tempfile.mkdtemp(prefix="fastblog_build_"))
        self.release_dir = self.output_dir / f"fastblog-v{version}"
        self.release_dir.mkdir(parents=True, exist_ok=True)
        print(f"构建版本 {version} → {self.release_dir}")

    @staticmethod
    def get_file_hash(file_path: Path) -> str:
        sha = hashlib.sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha.update(chunk)
        return sha.hexdigest()

    def _copy_tree_collecting(self, src: Path, dst: Path) -> List[Path]:
        """复制目录并返回所有目标文件路径列表"""
        shutil.copytree(src, dst, dirs_exist_ok=True)
        return [p for p in dst.rglob("*") if p.is_file()]

    def _copy_file_collecting(self, src: Path, dst: Path) -> List[Path]:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return [dst]

    def copy_backend_files(self) -> List[Path]:
        print("复制后端文件...")
        files = []
        backend_dirs = [
            "src", "apps", "django_blog", "shared", "config",
            "process_supervisor", "updater", "update_server",
            "scripts", "docs", "static"
        ]
        for d in backend_dirs:
            src_dir = self.project_root / d
            if src_dir.exists():
                files.extend(self._copy_tree_collecting(src_dir, self.release_dir / d))
                print(f"已复制目录: {d}")

        backend_root_files = [
            "main.py", "requirements.txt", "version.txt",
            ".env_example", ".gitignore", "README.md", "LICENSE"
        ]
        for fname in backend_root_files:
            src = self.project_root / fname
            if src.exists():
                files.extend(self._copy_file_collecting(src, self.release_dir / fname))
        return files

    def build_frontend(self) -> List[Path]:
        print("构建前端 (Astro)...")
        frontend_dir = self.project_root / "frontend-astro"
        if not frontend_dir.exists():
            print("WARNING: frontend-astro 目录不存在，跳过前端构建")
            return []

        try:
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=frontend_dir,
                capture_output=True, text=True, timeout=300,
                encoding="utf-8", errors="replace"
            )
            if result.returncode != 0:
                print(f"ERROR: 前端构建失败: {result.stderr}")
                return []
            print("前端构建完成")

            files = []
            dist_src = frontend_dir / "dist"
            if dist_src.exists():
                dst_dist = self.release_dir / "frontend-astro" / "dist"
                files.extend(self._copy_tree_collecting(dist_src, dst_dist))

            # 复制配置文件
            config_files = [
                "package.json", "astro.config.mjs", "tsconfig.json",
                "tailwind.config.mjs", "postcss.config.mjs", ".env_example"
            ]
            for fname in config_files:
                src = frontend_dir / fname
                if src.exists():
                    dst = self.release_dir / "frontend-astro" / fname
                    files.extend(self._copy_file_collecting(src, dst))
            print(f"已收集 {len(files)} 个前端文件")
            return files
        except subprocess.TimeoutExpired:
            print("ERROR: 前端构建超时")
        except Exception as e:
            print(f"ERROR: 前端构建异常: {e}")
        return []

    def create_startup_scripts(self) -> List[Path]:
        print("创建启动脚本...")
        win_script = self.release_dir / "start.bat"
        win_script.write_text(
            f"@echo off\ncd /d \"%~dp0\"\npython main.py\npause\n",
            encoding="utf-8"
        )
        unix_script = self.release_dir / "start.sh"
        unix_script.write_text(
            f"#!/bin/bash\ncd \"$(dirname \"$0\")\"\npython3 main.py\n",
            encoding="utf-8"
        )
        unix_script.chmod(0o755)
        return [win_script, unix_script]

    def create_checksums(self, all_files: List[Path]) -> Path:
        print("创建校验和文件...")
        checksums = {}
        for f in all_files:
            try:
                rel = f.relative_to(self.release_dir).as_posix()
                checksums[rel] = self.get_file_hash(f)
            except Exception as e:
                print(f"WARNING: 哈希计算失败 {f}: {e}")

        checksum_file = self.release_dir / "CHECKSUMS.json"
        checksum_file.write_text(json.dumps(checksums, indent=2, ensure_ascii=False), encoding="utf-8")
        return checksum_file

    def parse_commit_message(self, subject: str) -> Optional[Dict]:
        pattern = r"^(?P<type>\w+)(?:\((?P<scope>[\w-]+)\))?(?P<breaking>!)?:\s*(?P<subject>.+)$"
        m = re.match(pattern, subject)
        if m:
            return {
                "type": m.group("type"),
                "scope": m.group("scope"),
                "breaking": bool(m.group("breaking")),
                "subject": m.group("subject").strip()
            }
        return None

    def get_commits_since_last_tag(self) -> List[Dict]:
        commits = []
        try:
            subprocess.run(["git", "rev-parse", "--git-dir"], check=True, capture_output=True)
            possible_tags = [f"v{self.version}", f"V{self.version}"]
            current_tag = None
            for tag in possible_tags:
                try:
                    subprocess.run(["git", "rev-parse", tag], check=True, capture_output=True)
                    current_tag = tag
                    break
                except subprocess.CalledProcessError:
                    continue
            if not current_tag:
                print(f"WARNING: 未找到版本标签 {possible_tags}")
                return commits

            prev_tag = ""
            try:
                res = subprocess.run(
                    ["git", "describe", "--tags", "--abbrev=0", f"{current_tag}^"],
                    check=True, capture_output=True, text=True, encoding="utf-8"
                )
                prev_tag = res.stdout.strip()
            except subprocess.CalledProcessError:
                pass

            rev_range = f"{prev_tag}..{current_tag}" if prev_tag else current_tag
            log = subprocess.run(
                ["git", "log", "--pretty=format:%H%n%s%n%b%n---", rev_range],
                check=True, capture_output=True, text=True, encoding="utf-8"
            )
            raw = log.stdout.strip()
            for entry in raw.split("\n---\n"):
                if not entry.strip():
                    continue
                lines = entry.strip().split("\n")
                if len(lines) >= 3:
                    commit_hash = lines[0][:8]
                    subject = lines[1]
                    body = "\n".join(lines[2:])
                    parsed = self.parse_commit_message(subject)
                    if parsed:
                        parsed["hash"] = commit_hash
                        parsed["body"] = body.strip()
                        commits.append(parsed)
        except Exception as e:
            print(f"WARNING: Git 信息获取失败: {e}")
        return commits

    def _format_commit_entry(self, c: Dict) -> str:
        scope = f"**{c['scope']}**: " if c.get("scope") else ""
        entry = f"- {scope}{c['subject']} ({c['hash']})"
        if c.get("body"):
            body_lines = [line.strip() for line in c["body"].split("\n") if line.strip()]
            if body_lines:
                entry += "\n" + "\n".join(f"    - {line}" for line in body_lines)
        return entry

    def create_release_notes(self) -> Path:
        print("生成发布说明...")
        commits = self.get_commits_since_last_tag()
        features, fixes, perfs, docs, breaking = [], [], [], [], []
        for c in commits:
            entry = self._format_commit_entry(c)
            if c["breaking"]:
                breaking.append(entry)
            if c["type"] == "feat":
                features.append(entry)
            elif c["type"] == "fix":
                fixes.append(entry)
            elif c["type"] == "docs":
                docs.append(entry)
            elif c["type"] == "perf":
                perfs.append(entry)

        if not features: features = ["- [在此处添加新功能描述]"]
        if not fixes: fixes = ["- [在此处添加修复的问题]"]
        if not perfs: perfs = ["- [在此处添加性能改进]"]
        if not breaking: breaking = ["- 无破坏性变更"]

        notes = f"""# FastBlog v{self.version} 发布说明

## 🎉 新特性
{chr(10).join(features)}

## 🚀 性能优化
{chr(10).join(perfs)}

## 📚 文档更新
{chr(10).join(docs) if docs else "无"}

## 🐛 问题修复
{chr(10).join(fixes)}

## ⚠️ 破坏性变更
{chr(10).join(breaking)}

## 🔧 技术栈版本

### 后端
{format_version_list(get_backend_versions())}

### 前端 (Astro)
{format_version_list(get_frontend_versions())}

## 📦 安装说明
请参考 README.md 获取详细安装配置说明。

---
发布日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        notes_path = self.release_dir / "RELEASE_NOTES.md"
        notes_path.write_text(notes, encoding="utf-8")
        return notes_path

    def create_zip_package(self) -> Path:
        print("打包 ZIP...")
        zip_path = self.output_dir / f"fastblog-v{self.version}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in self.release_dir.rglob("*"):
                if f.is_file():
                    arcname = f.relative_to(self.output_dir)
                    zf.write(f, arcname)
        print(f"ZIP 已创建: {zip_path} ({zip_path.stat().st_size / 1024 / 1024:.2f} MB)")
        return zip_path

    def build(self) -> Dict:
        start = time.time()
        try:
            files = []
            files.extend(self.copy_backend_files())
            files.extend(self.build_frontend())
            files.extend(self.create_startup_scripts())

            checksum_file = self.create_checksums(files)
            files.append(checksum_file)

            release_notes = self.create_release_notes()
            files.append(release_notes)

            zip_file = self.create_zip_package()
            zip_hash = self.get_file_hash(zip_file)
            (self.output_dir / f"fastblog-v{self.version}-checksum.txt").write_text(
                f"{zip_hash}  fastblog-v{self.version}.zip\n", encoding="utf-8"
            )

            elapsed = time.time() - start
            result = {
                "success": True,
                "version": self.version,
                "files_count": len(files),
                "zip_file": str(zip_file),
                "zip_size_mb": round(zip_file.stat().st_size / 1048576, 2),
                "build_time_seconds": round(elapsed, 2),
                "release_dir": str(self.release_dir)
            }
            print(f"构建完成，耗时 {elapsed:.2f}s")
            return result
        except Exception as e:
            print(f"ERROR: 构建失败: {e}")
            return {"success": False, "error": str(e)}
        finally:
            shutil.rmtree(self.build_temp, ignore_errors=True)


# ---------- 增量更新包构建器 ----------
class UpdatePackageBuilder:
    def __init__(self, version: str, output_dir: str = "releases"):
        self.version = version
        self.output_dir = Path(output_dir)
        self.project_root = project_root
        self.build_temp = Path(tempfile.mkdtemp(prefix="fastblog_update_"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_changed_files(self, base_version: str) -> List[str]:
        try:
            res = subprocess.run(
                ["git", "diff", "--name-only", f"v{base_version}", f"v{self.version}"],
                cwd=self.project_root, capture_output=True, text=True, timeout=30
            )
            if res.returncode == 0:
                return [f.strip() for f in res.stdout.split("\n") if f.strip()]
        except Exception as e:
            print(f"ERROR: 获取变更文件失败: {e}")
        return []

    def collect_update_files(self, changed_files: List[str]) -> List[Path]:
        include_dirs = [
            "src", "apps", "django_blog", "shared", "config",
            "process_supervisor", "updater", "update_server",
            "scripts", "frontend-astro"  # 添加 Astro 源码目录
        ]
        include_root = ["main.py", "requirements.txt", "version.txt", ".env_example", "README.md"]
        files = []
        for path_str in changed_files:
            src = self.project_root / path_str
            if not src.exists():
                continue
            if any(path_str.startswith(d) for d in include_dirs) or path_str in include_root:
                files.append(src)
        return files

    def create_update_package(self, base_version: Optional[str] = None) -> Optional[Path]:
        print("创建增量更新包...")
        if not base_version:
            try:
                vf = self.project_root / "version.txt"
                if vf.exists():
                    for line in vf.read_text(encoding="utf-8").splitlines():
                        if line.strip().startswith("version="):
                            base_version = line.split("=", 1)[1].strip()
                            break
            except Exception:
                pass

        if base_version:
            changed = self.get_changed_files(base_version)
            update_files = self.collect_update_files(changed) if changed else []
        else:
            # 全量模式
            update_files = [p for d in ["src", "apps", "updater", "update_server"]
                            for p in (self.project_root / d).rglob("*") if p.is_file()]

        temp_dir = self.build_temp / f"update_{self.version}"
        temp_dir.mkdir(parents=True)
        for src in update_files:
            rel = src.relative_to(self.project_root)
            dst = temp_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        metadata = {
            "version": self.version,
            "base_version": base_version or "unknown",
            "build_time": datetime.now().isoformat(),
            "python_version": platform.python_version(),
            "files_count": len(update_files)
        }
        (temp_dir / "update_metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False))

        zip_path = self.output_dir / f"update_{self.version}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in temp_dir.rglob("*"):
                if f.is_file():
                    zf.write(f, f"update/{f.relative_to(temp_dir)}")

        sha = hashlib.sha256()
        with zip_path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha.update(chunk)
        (self.output_dir / f"update_{self.version}.sha256").write_text(
            f"{sha.hexdigest()}  update_{self.version}.zip\n", encoding="utf-8"
        )
        print(f"增量包已创建: {zip_path}")
        return zip_path

    def cleanup(self):
        shutil.rmtree(self.build_temp, ignore_errors=True)


def build_update_package(version: str, output_dir: str = "releases", base_version: str = None):
    builder = UpdatePackageBuilder(version, output_dir)
    try:
        return builder.create_update_package(base_version)
    finally:
        builder.cleanup()


# ---------- 主入口 ----------
def main():
    parser = argparse.ArgumentParser(description="FastBlog 发布构建工具 (Astro 版)")
    parser.add_argument("--version", "-v", required=True, help="版本号")
    parser.add_argument("--output", "-o", default="release", help="输出目录")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    args = parser.parse_args()

    builder = ReleaseBuilder(args.version, args.output)
    result = builder.build()

    if result.get("success"):
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)
    else:
        print(f"构建失败: {result.get('error')}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
