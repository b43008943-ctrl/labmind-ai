"""
LabMind AI — Storage Provider (Abstract)
Defines the interface for file storage backends.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class StorageProvider(ABC):
    """Abstract interface for file storage."""

    @abstractmethod
    def upload(self, key: str, data: bytes, content_type: str | None = None) -> str:
        """Store file data under the given key. Returns the storage key."""
        ...

    @abstractmethod
    def download(self, key: str) -> bytes:
        """Retrieve file data by key."""
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove a file by key."""
        ...

    @abstractmethod
    def get_url(self, key: str) -> str:
        """Return a URL/path to access the file."""
        ...
