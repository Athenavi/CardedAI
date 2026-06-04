"""
IPFS 去中心化存储服务
提供文件上传、下载、固定等功能

注意：需要运行本地 IPFS 节点或使用远程 IPFS 服务
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List


@dataclass
class IPFSFile:
    """IPFS 文件信息"""
    cid: str  # Content ID (哈希值)
    filename: str  # 文件名
    size: int  # 文件大小（字节）
    content_type: str  # MIME 类型
    uploaded_at: str  # 上传时间
    pinned: bool = False  # 是否已固定
    gateway_url: str = ""  # 网关访问 URL


class IPFSService:
    """
    IPFS 存储服务
    
    功能：
    1. 上传文件到 IPFS
    2. 从 IPFS 下载文件
    3. 固定重要文件（防止被垃圾回收）
    4. 批量上传和管理
    
    配置方式：
    - 使用本地 IPFS 节点：http://localhost:5001
    - 使用远程服务：Infura, Pinata, Web3.Storage 等
    """

    def __init__(self):
        # IPFS 配置
        self.config = {
            "api_url": "http://localhost:5001",  # IPFS API 地址
            "gateway_url": "https://ipfs.io/ipfs/",  # IPFS 网关
            "api_key": "",  # API Key（如使用 Pinata）
            "api_secret": "",  # API Secret
            "pinata_jwt": "",  # Pinata JWT Token
            "auto_pin": True,  # 自动固定上传的文件
        }

        # 文件记录（实际应使用数据库）
        self.file_records: Dict[str, IPFSFile] = {}

    def upload_file(self, file_content: bytes, filename: str, content_type: str = "application/octet-stream") -> \
    Optional[IPFSFile]:
        """
        上传文件到 IPFS
        
        Args:
            file_content: 文件内容（字节）
            filename: 文件名
            content_type: MIME 类型
            
        Returns:
            IPFS 文件信息，失败返回 None
        """
        try:
            # 计算文件哈希（作为 CID）
            cid = hashlib.sha256(file_content).hexdigest()

            # 在实际实现中，这里应该：
            # 1. 调用 IPFS API 上传文件
            # 2. 获取返回的 CID
            # 3. 如果需要，固定文件

            # 模拟上传过程
            print(f"📤 上传文件到 IPFS: {filename}")
            print(f"   大小: {len(file_content)} bytes")
            print(f"   CID: {cid}")

            # 创建文件记录
            ipfs_file = IPFSFile(
                cid=cid,
                filename=filename,
                size=len(file_content),
                content_type=content_type,
                uploaded_at=datetime.now().isoformat(),
                pinned=self.config.get("auto_pin", False),
                gateway_url=f"{self.config['gateway_url']}{cid}"
            )

            # 保存记录
            self.file_records[cid] = ipfs_file

            # 如果需要自动固定
            if self.config.get("auto_pin", False):
                self.pin_file(cid)

            print(f"✅ 文件上传成功: {ipfs_file.gateway_url}")

            return ipfs_file

        except Exception as e:
            print(f"❌ 文件上传失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def upload_text(self, text: str, filename: str = "content.txt") -> Optional[IPFSFile]:
        """
        上传文本内容到 IPFS
        
        Args:
            text: 文本内容
            filename: 文件名
            
        Returns:
            IPFS 文件信息
        """
        content = text.encode('utf-8')
        return self.upload_file(content, filename, "text/plain")

    def upload_json(self, data: Dict[str, Any], filename: str = "data.json") -> Optional[IPFSFile]:
        """
        上传 JSON 数据到 IPFS
        
        Args:
            data: JSON 数据
            filename: 文件名
            
        Returns:
            IPFS 文件信息
        """
        content = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
        return self.upload_file(content, filename, "application/json")

    def upload_article(self, article_data: Dict[str, Any]) -> Optional[IPFSFile]:
        """
        上传文章内容到 IPFS
        
        Args:
            article_data: 文章数据 {id, title, content, author, ...}
            
        Returns:
            IPFS 文件信息
        """
        # 准备元数据
        metadata = {
            "type": "article",
            "version": "1.0",
            "article_id": article_data.get("id"),
            "title": article_data.get("title"),
            "author": article_data.get("author"),
            "content": article_data.get("content"),
            "created_at": article_data.get("created_at", datetime.now().isoformat()),
            "tags": article_data.get("tags", [])
        }

        filename = f"article_{article_data.get('id', 'unknown')}.json"
        return self.upload_json(metadata, filename)

    def download_file(self, cid: str) -> Optional[bytes]:
        """
        从 IPFS 下载文件
        
        Args:
            cid: 内容 ID
            
        Returns:
            文件内容（字节），失败返回 None
        """
        try:
            # 在实际实现中，这里应该：
            # 1. 通过 IPFS 网关或 API 获取文件
            # 2. 返回文件内容

            print(f"📥 从 IPFS 下载文件: {cid}")

            # 模拟下载
            if cid in self.file_records:
                print(f"✅ 文件下载成功")
                return b"simulated content"
            else:
                print(f"⚠️ 文件不存在: {cid}")
                return None

        except Exception as e:
            print(f"❌ 文件下载失败: {e}")
            return None

    def pin_file(self, cid: str) -> bool:
        """
        固定文件（防止被垃圾回收）
        
        Args:
            cid: 内容 ID
            
        Returns:
            是否固定成功
        """
        try:
            # 在实际实现中，这里应该调用 IPFS pin API

            if cid in self.file_records:
                self.file_records[cid].pinned = True
                print(f"📌 文件已固定: {cid}")
                return True
            else:
                print(f"⚠️ 文件不存在: {cid}")
                return False

        except Exception as e:
            print(f"❌ 固定文件失败: {e}")
            return False

    def unpin_file(self, cid: str) -> bool:
        """
        取消固定文件
        
        Args:
            cid: 内容 ID
            
        Returns:
            是否取消成功
        """
        try:
            if cid in self.file_records:
                self.file_records[cid].pinned = False
                print(f"🔓 文件已取消固定: {cid}")
                return True
            else:
                print(f"⚠️ 文件不存在: {cid}")
                return False

        except Exception as e:
            print(f"❌ 取消固定失败: {e}")
            return False

    def get_file_info(self, cid: str) -> Optional[Dict[str, Any]]:
        """
        获取文件信息
        
        Args:
            cid: 内容 ID
            
        Returns:
            文件信息字典
        """
        if cid not in self.file_records:
            return None

        file_info = self.file_records[cid]

        return {
            "cid": file_info.cid,
            "filename": file_info.filename,
            "size": file_info.size,
            "content_type": file_info.content_type,
            "uploaded_at": file_info.uploaded_at,
            "pinned": file_info.pinned,
            "gateway_url": file_info.gateway_url
        }

    def list_files(self, pinned_only: bool = False) -> List[Dict[str, Any]]:
        """
        列出所有文件
        
        Args:
            pinned_only: 是否只列出已固定的文件
            
        Returns:
            文件列表
        """
        files = []

        for cid, file_info in self.file_records.items():
            if pinned_only and not file_info.pinned:
                continue

            files.append({
                "cid": cid,
                "filename": file_info.filename,
                "size": file_info.size,
                "pinned": file_info.pinned,
                "gateway_url": file_info.gateway_url
            })

        return files

    def delete_file(self, cid: str) -> bool:
        """
        删除文件记录（仅本地记录，IPFS 上的文件无法真正删除）
        
        Args:
            cid: 内容 ID
            
        Returns:
            是否删除成功
        """
        if cid in self.file_records:
            del self.file_records[cid]
            print(f"🗑️ 文件记录已删除: {cid}")
            return True
        else:
            return False

    def configure(self, config: Dict[str, str]):
        """
        配置 IPFS 服务
        
        Args:
            config: 配置字典
        """
        self.config.update(config)
        print("✅ IPFS 服务配置已更新")
        print(f"   API URL: {self.config.get('api_url')}")
        print(f"   Gateway: {self.config.get('gateway_url')}")


# 全局实例
ipfs_service = IPFSService()
