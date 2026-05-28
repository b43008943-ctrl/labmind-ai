"""
LabMind AI — Local Filesystem Storage Provider
Development-mode storage that saves files to a local directory.
"""

from pathlib import Path

from app.providers.storage_provider import StorageProvider


class LocalStorageProvider(StorageProvider):
    """Stores files on the local filesystem under a configurable root directory."""

    def __init__(self, root_dir: str = "uploads"):
        self.root = Path(root_dir).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def upload(self, key: str, data: bytes, content_type: str | None = None) -> str:
        file_path = self.root / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)
        return key

    def download(self, key: str) -> bytes:
        file_path = self.root / key
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {key}")
        return file_path.read_bytes()

    def delete(self, key: str) -> None:
        file_path = self.root / key
        if file_path.exists():
            file_path.unlink()

    def get_url(self, key: str) -> str:
        return f"/uploads/{key}"
