"""Random sampling strategy."""

from __future__ import annotations

import random
from typing import Any

from .base import SamplingStrategy


class RandomSampling(SamplingStrategy):
    """Pure random sampling strategy."""

    def __init__(self, seed: int | None = None, allow_duplicates: bool = False):
        self.seed = seed
        self.allow_duplicates = allow_duplicates
        if seed is not None:
            random.seed(seed)

    def sample(self, data: list[dict], sample_size: int, **kwargs) -> list[dict]:
        if sample_size >= len(data):
            return data.copy()

        if self.allow_duplicates:
            return [random.choice(data) for _ in range(sample_size)]

        return random.sample(data, sample_size)
