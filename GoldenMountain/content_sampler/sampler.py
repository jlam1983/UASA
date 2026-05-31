"""Main content sampler."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .strategies import get_strategy, STRATEGIES
from .schema_analyzer import SchemaAnalyzer
from .noise_labeler import NoiseLabeler


class ContentSampler:
    """Main content sampler with schema analysis and noise labeling."""

    def __init__(self, default_strategy: str = "random", seed: int | None = None):
        self.default_strategy = default_strategy
        self.seed = seed
        self._noise_labeler = None

    def sample(
        self,
        data: list[dict],
        sample_size: int,
        strategy: str | None = None,
        **kwargs
    ) -> list[dict]:
        """Sample data using specified strategy."""
        strategy_name = strategy or self.default_strategy

        try:
            sampler = get_strategy(strategy_name, **kwargs)
        except Exception:
            sampler = get_strategy("random", seed=self.seed)
            strategy_name = "random"

        sampled = sampler.sample(data, sample_size, **kwargs)

        # Add sample metadata without modifying original data
        return [
            {**record, "_sample_index": i, "_sample_strategy": strategy_name}
            for i, record in enumerate(sampled)
        ]

    def sample_with_analysis(
        self,
        data: list[dict],
        sample_size: int,
        strategy: str | None = None,
        analyze_schema: bool = True,
        detect_noise: bool = False,
        **kwargs
    ) -> dict:
        """Sample data with optional schema analysis and noise detection."""
        sampled = self.sample(data, sample_size, strategy, **kwargs)

        result = {
            "metadata": {
                "original_count": len(data),
                "sample_size": sample_size,
                "strategy": strategy or self.default_strategy,
                "sampled_at": datetime.utcnow().isoformat() + "Z"
            },
            "records": [{"_id": f"sample_{i}", "_source": r} for i, r in enumerate(sampled)]
        }

        if analyze_schema:
            analyzer = SchemaAnalyzer()
            # Filter out sample metadata fields for schema analysis
            sampled_for_analysis = [
                {k: v for k, v in r.items() if k not in ("_sample_index", "_sample_strategy")}
                for r in sampled
            ]
            schema_info = analyzer.analyze(sampled_for_analysis)
            result["schema_analysis"] = schema_info

        if detect_noise:
            labeler = NoiseLabeler()
            noise_report = labeler.detect_and_label(sampled)
            result["noise_report"] = noise_report["noise_report"]

        return result

    def analyze_schema(self, data: list[dict]) -> dict:
        """Analyze schema of data."""
        analyzer = SchemaAnalyzer()
        return analyzer.analyze(data)

    def optimize_schema(self, schema_analysis: dict, target: str = "sqlite") -> dict:
        """Optimize schema for target database."""
        analyzer = SchemaAnalyzer()
        return analyzer.optimize(schema_analysis, target)

    def detect_noise(self, data: list[dict]) -> dict:
        """Detect noise in data."""
        self._noise_labeler = NoiseLabeler()
        return self._noise_labeler.detect_and_label(data)

    def clean_data(self, data: list[dict], remove_labeled: bool = True) -> list[dict]:
        """Clean data by removing labeled noise."""
        if self._noise_labeler is None:
            self._noise_labeler = NoiseLabeler()
            self._noise_labeler.detect_and_label(data)
        return self._noise_labeler.clean(data, remove_labeled=remove_labeled)
