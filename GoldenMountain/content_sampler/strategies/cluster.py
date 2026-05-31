"""Cluster sampling strategy."""

from __future__ import annotations

import random
from .base import SamplingStrategy


class ClusterSampling(SamplingStrategy):
    """Cluster sampling - hash-based cluster centers."""

    def __init__(self, n_clusters: int = 5, seed: int | None = None):
        self.n_clusters = n_clusters
        if seed is not None:
            random.seed(seed)

    def sample(self, data: list[dict], sample_size: int, **kwargs) -> list[dict]:
        if sample_size >= len(data):
            return data.copy()

        if len(data) <= sample_size:
            return data.copy()

        clusters: dict[int, list[dict]] = {}
        for record in data:
            cluster_id = hash(str(record)) % self.n_clusters
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(record)

        sampled = []
        for cluster_records in clusters.values():
            proportion = len(cluster_records) / len(data)
            cluster_size = max(1, int(sample_size * proportion))
            cluster_sampled = random.sample(
                cluster_records, min(cluster_size, len(cluster_records)))
            sampled.extend(cluster_sampled)

        return sampled[:sample_size]
