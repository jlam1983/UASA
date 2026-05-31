"""Custom exceptions for data ingestion."""


class IngestionError(Exception):
    """Base exception for ingestion errors."""
    pass


class ChannelReadError(IngestionError):
    """Failed to read from channel."""
    pass


class ParseError(IngestionError):
    """Failed to parse data."""
    pass


class NormalizationError(IngestionError):
    """Failed to normalize data."""
    pass


class ChannelNotFoundError(IngestionError):
    """Channel adapter not found."""
    pass


class FileTypeNotSupportedError(IngestionError):
    """File type not supported."""
    pass
