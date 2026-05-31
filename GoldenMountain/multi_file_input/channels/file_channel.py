"""File channel adapter.

Each channel has exactly 2 methods:
- read(path) -> bytes | dict (input)
- export(path, data) -> dict (output as normalized JSON)
"""

import os
import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Generator

from ..exceptions import ChannelReadError


class FileEventType(Enum):
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass
class FileEvent:
    type: FileEventType
    path: str
    size: int
    timestamp: float


class FileChannel:
    """Handles file uploads from web forms, API multipart, or local files."""

    MAGIC_BYTES = {
        b"\xef\xbb\xbf": "csv",  # UTF-8 BOM
        b"PK": "xlsx",  # ZIP-based (Office)
        b"%PDF": "pdf",
        b"\xd0\xcf\xed": "xls",  # Old Excel
    }

    def __init__(self, watch_interval: float = 1.0):
        self.watch_interval = watch_interval

    def read(self, file_path: str, normalize_line_endings: bool = True) -> bytes:
        """Read file content as bytes.

        Args:
            file_path: Path to file to read

        Returns:
            File content as bytes
        """
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            if normalize_line_endings:
                content = content.replace(b"\r\n", b"\n")
            return content
        except FileNotFoundError as e:
            raise ChannelReadError(f"File not found: {file_path}") from e
        except PermissionError as e:
            raise ChannelReadError(f"Permission denied: {file_path}") from e
        except Exception as e:
            raise ChannelReadError(f"Failed to read file {file_path}: {e}") from e

    def export(self, file_path: str, data: dict) -> dict:
        """Write normalized JSON to file.

        Args:
            file_path: Destination file path
            data: Normalized JSON dict (metadata + records)

        Returns:
            The data written (for chaining)
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return data
        except Exception as e:
            raise ChannelReadError(f"Failed to write file {file_path}: {e}") from e

    def detect_type(self, file_path: str) -> str:
        """Detect file type from extension and magic bytes."""
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")

        if ext in ("xlsx", "xlsm"):
            return "xlsx"
        if ext in ("docx", "pptx"):
            return ext

        try:
            with open(file_path, "rb") as f:
                header = f.read(4)
        except FileNotFoundError:
            return ext or "unknown"

        for magic, ftype in self.MAGIC_BYTES.items():
            if header.startswith(magic):
                return ftype

        if ext in ("csv", "json", "xml", "yaml", "yml", "txt", "parquet", "avro"):
            return ext

        return ext or "unknown"

    def watch(self, directory: str) -> Generator[FileEvent, None, None]:
        """Watch directory for new files."""
        import time

        watched = {}
        while True:
            try:
                for entry in os.scandir(directory):
                    if not entry.is_file():
                        continue

                    stat = entry.stat()
                    mtime = stat.st_mtime

                    if entry.name not in watched:
                        watched[entry.name] = mtime
                        yield FileEvent(
                            type=FileEventType.CREATED,
                            path=entry.path,
                            size=stat.st_size,
                            timestamp=mtime,
                        )
                    elif watched[entry.name] != mtime:
                        watched[entry.name] = mtime
                        yield FileEvent(
                            type=FileEventType.MODIFIED,
                            path=entry.path,
                            size=stat.st_size,
                            timestamp=mtime,
                        )

            except FileNotFoundError:
                pass

            time.sleep(self.watch_interval)

    def batch_read(self, directory: str, pattern: str = "*") -> list[tuple[str, bytes]]:
        """Read all files in directory matching pattern."""
        import glob

        files = []
        for path in glob.glob(os.path.join(directory, pattern)):
            if os.path.isfile(path):
                files.append((path, self.read(path)))
        return files

    def compute_hash(self, file_path: str) -> str:
        """Compute MD5 hash of file."""
        with open(file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
