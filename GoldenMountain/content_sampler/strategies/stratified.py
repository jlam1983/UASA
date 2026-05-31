"""Stratified sampling strategy."""

from __future__ import annotations

import random
from typing import Any

from .base import SamplingStrategy


class StratifiedSampling(SamplingStrategy):
    """Stratified sampling - maintains proportions of a key."""

    def __init__(self, stratify_by: str | None = None, seed: int | None = None):
        self.stratify_by = stratify_by
        if seed is not None:
            random.seed(seed)

    def sample(self, data: list[dict], sample_size: int, **kwargs) -> list[dict]:
        if not data:
            return []

        if not self.stratify_by:
            from .random import RandomSampling
            return RandomSampling(seed=None).sample(data, sample_size)

        groups: dict[Any, list[dict]] = {}
        for record in data:
            key_value = record.get(self.stratify_by)
            if key_value not in groups:
                groups[key_value] = []
            groups[key_value].append(record)

        total = len(data)
        sampled = []

        for key, group_records in groups.items():
            proportion = len(group_records) / total
            group_sample_size = max(1, round(sample_size * proportion))
            group_sampled = random.sample(
                group_records, min(group_sample_size, len(group_records))
            )
            sampled.extend(group_sampled)

        return sampled


class RandomSampling:
    """Helper for stratified sampling."""
    def __init__(self, seed=None):
        if seed is not None:
            random.seed(seed)

    def sample(self, data, sample_size):
        if sample_size >= len(data):
            return data.copy()
        return random.sample(data, sample_size)
