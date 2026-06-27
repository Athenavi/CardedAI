"""
Local filesystem fallback for the (missing) real S3 storage module.

Provides the same interface expected by all callers:
    save_file(file_hash, file_data, original_filename) -> str
    save_raw_file(path, data) -> None
    read_file(path) -> bytes | None
    delete_file(storage_path) -> bool

All files are stored under a configurable base directory (default: ./storage).
"""

import os
from pathlib import Path
from typing import Optional


class LocalStorage:
    """Local filesystem storage that mimics an S3-like interface."""

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            base_dir = os.environ.get(
                "STORAGE_BASE_DIR",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "storage"),
            )
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, relative_path: str) -> Path:
        """Resolve a relative path against the base directory, preventing escape."""
        clean = relative_path.lstrip("/")
        if clean.startswith("s3://"):
            clean = clean[5:].lstrip("/")
        target = (self.base_dir / clean).resolve()
        if not str(target).startswith(str(self.base_dir)):
            raise ValueError(f"Path traversal detected: {relative_path}")
        return target

    def save_file(self, file_hash: str, file_data: bytes, original_filename: str) -> str:
        """Save a file using its hash as the primary key."""
        ext = ""
        if original_filename and "." in original_filename:
            ext = "." + original_filename.rsplit(".", 1)[-1]
        relative = f"objects/{file_hash[:2]}/{file_hash}{ext}"
        full_path = self._resolve(relative)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(file_data)
        return relative

    def save_raw_file(self, path: str, data: bytes) -> None:
        """Save raw data at an exact relative path."""
        full_path = self._resolve(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(data)

    def read_file(self, path: str) -> Optional[bytes]:
        """Read a file from the given relative path."""
        full_path = self._resolve(path)
        if not full_path.is_file():
            return None
        return full_path.read_bytes()

    def delete_file(self, storage_path: str) -> bool:
        """Delete a file at the given relative path."""
        full_path = self._resolve(storage_path)
        if not full_path.is_file():
            return False
        try:
            full_path.unlink()
            return True
        except OSError:
            return False


# Singleton instance — matches `from ... s3_storage import s3_storage`
s3_storage = LocalStorage()
