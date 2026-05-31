"""Normalization strategies for numeric values."""


class Normalizer:
    """Normalize numeric values using various scaling methods."""

    def min_max_scale(
        self,
        values: list[float],
        min_val: float = None,
        max_val: float = None
    ) -> list[float]:
        """Scale values to range [0, 1] using min-max scaling."""
        min_val = min_val if min_val is not None else min(values)
        max_val = max_val if max_val is not None else max(values)
        range_val = max_val - min_val
        if range_val == 0:
            return [0.5] * len(values)
        return [(v - min_val) / range_val for v in values]

    def z_score_scale(self, values: list[float]) -> list[float]:
        """Scale values to mean=0, std=1 using z-score normalization."""
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = variance ** 0.5
        if std == 0:
            return [0.0] * len(values)
        return [(v - mean) / std for v in values]

    def robust_scale(self, values: list[float]) -> list[float]:
        """Scale values using median and IQR (robust to outliers)."""
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        median = sorted_vals[n // 2]
        q1 = sorted_vals[n // 4]
        q3 = sorted_vals[n // 4 * 3]
        iqr = q3 - q1
        if iqr == 0:
            return [0.0] * len(values)
        return [(v - median) / iqr for v in values]

    def normalize(
        self,
        records: list[dict],
        fields: list[str],
        method: str = "min_max"
    ) -> list[dict]:
        """Normalize specified numeric fields in records."""
        result = []
        for record in records:
            new_record = dict(record)
            for field in fields:
                if field in record and record[field] is not None:
                    try:
                        vals = [r[field] for r in records if field in r and r[field] is not None]
                        if method == "min_max":
                            scaled = self.min_max_scale(vals)
                        elif method == "z_score":
                            scaled = self.z_score_scale(vals)
                        elif method == "robust":
                            scaled = self.robust_scale(vals)
                        else:
                            scaled = self.min_max_scale(vals)
                        # Apply scaled values
                        idx = 0
                        for i, r in enumerate(records):
                            if field in r and r[field] is not None:
                                if i == list(records).index(record):
                                    new_record[f"{field}_normalized"] = scaled[idx]
                                    break
                                idx += 1
                    except (TypeError, ValueError):
                        pass
            result.append(new_record)
        return result