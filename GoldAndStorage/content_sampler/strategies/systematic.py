"""Systematic sampling strategy."""

from __future__ import annotations

from .base import SamplingStrategy


class SystematicSampling(SamplingStrategy):
    """Systematic sampling - every Nth record."""

    def __init__(self, interval: int | None = None):
        self.interval = interval

    def sample(self, data: list[dict], sample_size: int, **kwargs) -> list[dict]:
        if not data:
            return []

        if sample_size >= len(data):
            return data.copy()

        interval = self.interval or max(1, len(data) // sample_size)
        sampled = []
        for i in range(0, len(data), interval):
            sampled.append(data[i])
            if len(sampled) >= sample_size:
                break

        return sampled
