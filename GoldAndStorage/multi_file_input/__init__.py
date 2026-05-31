"""Multi-File Type Input System.

A flexible data ingestion layer that reads from multiple file types and channels,
normalizing everything to a common JSON format for downstream processing.
"""

from .exceptions import (
    IngestionError,
    ChannelReadError,
    ParseError,
    NormalizationError,
    ChannelNotFoundError,
    FileTypeNotSupportedError,
)
from .adapters import (
    FileTypeAdapter,
    CSVAdapter,
    JSONAdapter,
    XMLAdapter,
    ExcelAdapter,
    YAMLAdapter,
    ParquetAdapter,
    AvroAdapter,
)
from .channels import (
    FileChannel,
    APIChannel,
    StreamChannel,
    IoTChannel,
    DatabaseChannel,
)
from .normalizer import JSONNormalizer
from .pipeline import DataIngestionPipeline, ChannelAdapterFactory

__version__ = "1.0.0"

__all__ = [
    "IngestionError",
    "ChannelReadError",
    "ParseError",
    "NormalizationError",
    "ChannelNotFoundError",
    "FileTypeNotSupportedError",
    "FileTypeAdapter",
    "CSVAdapter",
    "JSONAdapter",
    "XMLAdapter",
    "ExcelAdapter",
    "YAMLAdapter",
    "ParquetAdapter",
    "AvroAdapter",
    "FileChannel",
    "APIChannel",
    "StreamChannel",
    "IoTChannel",
    "DatabaseChannel",
    "JSONNormalizer",
    "DataIngestionPipeline",
    "ChannelAdapterFactory",
]
