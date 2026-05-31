"""Configuration management."""

from __future__ import annotations

import os
import yaml
from typing import Any
from dataclasses import dataclass, field


@dataclass
class FileChannelConfig:
    watch_directories: list[str] = field(default_factory=list)
    auto_detect_type: bool = True


@dataclass
class APIChannelConfig:
    base_url: str = ""
    timeout: int = 30
    retry_count: int = 3
    auth_type: str = "bearer"
    token_url: str = ""


@dataclass
class StreamChannelConfig:
    type: str = "kafka"
    bootstrap_servers: list[str] = field(default_factory=lambda: ["localhost:9092"])
    consumer_group: str = "data_processor"


@dataclass
class IoTChannelConfig:
    platform: str = "aws_iot"
    region: str = "us-east-1"
    edge_compute: bool = False


@dataclass
class DatabaseChannelConfig:
    poll_interval: int = 60
    change_detection: bool = True


@dataclass
class CSVConfig:
    delimiter: str = ","
    encoding: str = "utf-8"
    has_header: bool = True


@dataclass
class ExcelConfig:
    sheet: int = 0
    has_header: bool = True


@dataclass
class NormalizerConfig:
    include_raw: bool = False
    generate_ids: bool = True
    snake_case_keys: bool = True


@dataclass
class Config:
    channels: dict[str, Any] = field(default_factory=dict)
    file_types: dict[str, Any] = field(default_factory=dict)
    normalizer: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str) -> "Config":
        """Load configuration from YAML file."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, path: str) -> None:
        """Save configuration to YAML file."""
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self.__dict__, f, default_flow_style=False)


def load_config(config_path: str | None = None) -> Config:
    """Load configuration from file or return default."""
    if config_path and os.path.exists(config_path):
        return Config.from_yaml(config_path)
    return Config()
