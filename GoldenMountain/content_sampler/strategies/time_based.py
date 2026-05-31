"""Time-based sampling strategy."""

from datetime import datetime
from .base import SamplingStrategy


class TimeBasedSampling(SamplingStrategy):
    """Time-based sampling - sample at intervals or windows."""

    def __init__(self, timestamp_field: str = "timestamp", interval: int = 1):
        self.timestamp_field = timestamp_field
        self.interval = interval

    def sample(self, data: list[dict], sample_size: int, **kwargs) -> list[dict]:
        if not data:
            return []

        def get_timestamp(record):
            value = record.get(self.timestamp_field, "")
            if isinstance(value, datetime):
                return value
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    return datetime.min
            return datetime.min

        sorted_data = sorted(data, key=get_timestamp)

        if len(sorted_data) <= sample_size:
            return sorted_data.copy()

        step = len(sorted_data) / sample_size
        sampled = []
        for i in range(sample_size):
            idx = min(int(i * step), len(sorted_data) - 1)
            sampled.append(sorted_data[idx])

        return sampled
