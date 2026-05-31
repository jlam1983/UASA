"""Categorical encoding strategies."""

from typing import List, Dict


class CategoricalEncoder:
    """Encode categorical variables as numeric values."""

    def label_encode(self, values: list[str]) -> list[int]:
        """Encode unique values as integers (0 to n-1)."""
        unique = list(set(values))
        return [unique.index(v) for v in values]

    def one_hot_encode(self, records: list[dict], field: str) -> list[dict]:
        """Encode categorical field as one-hot binary columns."""
        unique_values = sorted(set(r[field] for r in records if field in r))
        result = []
        for record in records:
            encoded = dict(record)
            for val in unique_values:
                encoded[f"{field}_{val}"] = 1 if record.get(field) == val else 0
            result.append(encoded)
        return result

    def target_encode(
        self,
        records: list[dict],
        category_field: str,
        target_field: str
    ) -> dict:
        """Encode categories by mean target value."""
        category_stats = {}
        for record in records:
            cat = record.get(category_field)
            target = record.get(target_field)
            if cat is None or target is None:
                continue
            if cat not in category_stats:
                category_stats[cat] = {"sum": 0, "count": 0}
            category_stats[cat]["sum"] += target
            category_stats[cat]["count"] += 1
        return {
            cat: stats["sum"] / stats["count"]
            for cat, stats in category_stats.items()
        }

    def encode(
        self,
        records: list[dict],
        field: str,
        method: str = "label"
    ) -> list[dict]:
        """Apply categorical encoding to records."""
        if method == "label":
            values = [r.get(field) for r in records if field in r]
            encoded_map = {v: i for i, v in enumerate(set(values))}
            for record in records:
                record[f"{field}_encoded"] = encoded_map.get(record.get(field))
            return records
        elif method == "one_hot":
            return self.one_hot_encode(records, field)
        else:
            return records