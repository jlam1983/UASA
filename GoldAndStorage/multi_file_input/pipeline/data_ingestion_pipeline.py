"""Data ingestion pipeline."""

from __future__ import annotations

import json
from typing import Any

from ..channels import (
    FileChannel,
    APIChannel,
    StreamChannel,
    IoTChannel,
    DatabaseChannel,
)
from ..adapters import (
    CSVAdapter,
    JSONAdapter,
    XMLAdapter,
    ExcelAdapter,
    YAMLAdapter,
    ParquetAdapter,
    AvroAdapter,
    FileTypeAdapter,
)
from ..normalizer import JSONNormalizer
from ..exceptions import ChannelReadError, ParseError, NormalizationError


class ChannelAdapterFactory:
    """Factory for creating channel adapters."""

    _channels = {
        "file": FileChannel,
        "api": APIChannel,
        "stream": StreamChannel,
        "iot": IoTChannel,
        "database": DatabaseChannel,
    }

    _file_types = {
        "csv": CSVAdapter,
        "json": JSONAdapter,
        "xml": XMLAdapter,
        "xlsx": ExcelAdapter,
        "xls": ExcelAdapter,
        "yaml": YAMLAdapter,
        "yml": YAMLAdapter,
        "parquet": ParquetAdapter,
        "avro": AvroAdapter,
    }

    @classmethod
    def create_channel(cls, channel_type: str) -> Any:
        """Create channel adapter by type."""
        if channel_type not in cls._channels:
            raise ChannelReadError(f"Unknown channel type: {channel_type}")
        return cls._channels[channel_type]()

    @classmethod
    def create_file_adapter(cls, file_type: str) -> FileTypeAdapter:
        """Create file type adapter by extension."""
        if file_type not in cls._file_types:
            raise ParseError(f"Unknown file type: {file_type}")
        return cls._file_types[file_type]()

    @classmethod
    def detect_file_type(cls, file_path: str) -> str:
        """Detect file type from path."""
        import os
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")
        if ext in ("xlsx", "xlsm"):
            return "xlsx"
        return ext


class DataIngestionPipeline:
    """Complete pipeline for multi-source data ingestion."""

    def __init__(self, normalizer: JSONNormalizer | None = None):
        self.normalizer = normalizer or JSONNormalizer()
        self.channel_factory = ChannelAdapterFactory()

    def ingest(
        self,
        source: str,
        channel_type: str,
        file_type: str | None = None,
        **kwargs,
    ) -> dict:
        """Ingest data from any source and return normalized JSON."""
        try:
            channel = self.channel_factory.create_channel(channel_type)

            raw_data = self._read_from_channel(channel, source, **kwargs)

            if file_type is None and channel_type == "file":
                file_type = self.channel_factory.detect_file_type(source)

            if file_type:
                adapter = self.channel_factory.create_file_adapter(file_type)
                parsed_data = adapter.parse(raw_data)
            else:
                parsed_data = self._parse_raw_json(raw_data)

            normalized = self.normalizer.normalize(
                data=parsed_data,
                source_type=file_type or "json",
                source_channel=channel_type,
                source_path=source,
            )

            return normalized

        except ChannelReadError:
            raise
        except ParseError:
            raise
        except Exception as e:
            raise NormalizationError(f"Failed to normalize data: {e}") from e

    def _read_from_channel(self, channel: Any, source: str, **kwargs) -> bytes | dict:
        """Read data from specified channel."""
        if isinstance(channel, FileChannel):
            return channel.read(source)
        elif isinstance(channel, APIChannel):
            return channel.fetch(source, **kwargs)
        elif isinstance(channel, StreamChannel):
            return channel.consume(source, **kwargs)
        elif isinstance(channel, IoTChannel):
            return channel.subscribe(source, **kwargs)
        elif isinstance(channel, DatabaseChannel):
            return channel.execute(source, **kwargs)
        else:
            raise ChannelReadError(f"Unsupported channel type: {type(channel)}")

    def _parse_raw_json(self, raw_data: bytes | dict) -> list[dict]:
        """Parse raw data as JSON."""
        if isinstance(raw_data, dict):
            if "data" in raw_data:
                return raw_data["data"]
            return [raw_data]

        if isinstance(raw_data, bytes):
            raw_data = raw_data.decode("utf-8")

        try:
            data = json.loads(raw_data)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                for key in ["data", "records", "items", "results"]:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                return [data]
            return []
        except json.JSONDecodeError as e:
            raise ParseError(f"Failed to parse JSON: {e}") from e

    def ingest_batch(
        self,
        sources: list[tuple[str, str, str | None]],
    ) -> list[dict]:
        """Ingest multiple sources."""
        results = []
        for source, channel_type, file_type in sources:
            try:
                result = self.ingest(source, channel_type, file_type)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e), "source": source})
        return results

    def ingest_directory(
        self,
        directory: str,
        channel_type: str = "file",
        pattern: str = "*",
    ) -> list[dict]:
        """Ingest all files in a directory."""
        import os
        import glob

        results = []
        for path in glob.glob(os.path.join(directory, pattern)):
            if os.path.isfile(path):
                try:
                    result = self.ingest(path, channel_type)
                    results.append(result)
                except Exception as e:
                    results.append({"error": str(e), "source": path})
        return results
