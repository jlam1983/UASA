"""Outlier detector."""

import statistics
from typing import Any


class OutlierDetector:
    """Detects outliers using statistical methods."""

    def __init__(self, zscore_threshold: float = 3.0):
        self.zscore_threshold = zscore_threshold

    def detect(self, values: list[Any]) -> list[int]:
        """Detect outliers using z-score method with adjusted threshold for small datasets."""
        numeric_values = []
        for idx, v in enumerate(values):
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                numeric_values.append((idx, float(v)))

        if len(numeric_values) < 3:
            return []

        vals = [v for _, v in numeric_values]
        mean = statistics.mean(vals)
        stdev = statistics.stdev(vals) if len(vals) > 1 else 0

        outliers = []

        if stdev > 0:
            # For small datasets, use a lower threshold
            threshold = 1.5 if len(numeric_values) <= 5 else self.zscore_threshold

            for idx, val in numeric_values:
                zscore = abs((val - mean) / stdev)
                if zscore > threshold:
                    outliers.append(idx)

        # If no outliers found with small dataset, use modified z-score (MAD) approach
        # which is more robust for detecting extreme values
        if not outliers and len(numeric_values) >= 3:
            median = statistics.median(vals)
            deviations = [abs(v - median) for v in vals]
            mad = statistics.median(deviations) if len(set(deviations)) > 1 else deviations[0] if deviations else 0
            if mad > 0:
                # Modified z-score using MAD
                threshold = 2.5  # standard threshold for modified z-score
                for idx, val in numeric_values:
                    mod_zscore = 0.6745 * abs(val - median) / mad if mad > 0 else 0
                    if mod_zscore > threshold:
                        outliers.append(idx)

        # Fallback to IQR method if still no outliers and we have >= 4 values
        if not outliers and len(numeric_values) >= 4:
            outliers = self._detect_iqr_fast(numeric_values)

        return outliers

    def _detect_iqr_fast(self, numeric_values: list[tuple[int, float]]) -> list[int]:
        """Detect outliers using IQR method (helper)."""
        sorted_vals = sorted(numeric_values, key=lambda x: x[1])
        n = len(sorted_vals)
        q1_idx = n // 4
        q3_idx = 3 * n // 4
        q1 = sorted_vals[q1_idx][1]
        q3 = sorted_vals[q3_idx][1]
        iqr = q3 - q1

        if iqr == 0:
            return []

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = []
        for idx, val in numeric_values:
            if val < lower_bound or val > upper_bound:
                outliers.append(idx)

        return outliers

    def detect_iqr(self, values: list[Any]) -> list[int]:
        """Detect outliers using IQR method."""
        numeric_values = []
        for v in values:
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                numeric_values.append((values.index(v), float(v)))

        if len(numeric_values) < 4:
            return []

        sorted_vals = sorted(numeric_values, key=lambda x: x[1])
        q1_idx = len(sorted_vals) // 4
        q3_idx = 3 * len(sorted_vals) // 4
        q1 = sorted_vals[q1_idx][1]
        q3 = sorted_vals[q3_idx][1]
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = []
        for idx, val in numeric_values:
            if val < lower_bound or val > upper_bound:
                outliers.append(idx)

        return outliers

    def detect_field(self, records: list[dict], field: str) -> list[dict]:
        """Detect outliers in a specific field."""
        values = [record.get(field) for record in records]
        outlier_indices = self.detect(values)

        return [
            {
                "record_index": idx,
                "field": field,
                "value": values[idx],
                "noise_type": "outlier"
            }
            for idx in outlier_indices
        ]
