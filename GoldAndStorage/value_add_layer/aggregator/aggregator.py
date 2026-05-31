"""DataAggregator - Groups and summarizes data to produce aggregated datasets."""

from typing import List, Dict, Any, Optional


class DataAggregator:
    """Aggregates data using various aggregation functions."""

    def aggregate(
        self,
        records: List[dict],
        group_by: List[str],
        aggregations: Dict[str, str]
    ) -> List[dict]:
        """
        Aggregate records by grouping fields.

        Args:
            records: Input records
            group_by: Fields to group by
            aggregations: {output_field: "agg_func,field"} or {output_field: "agg_func"}

        Returns:
            Aggregated records
        """
        grouped = self._group_records(records, group_by)
        results = []
        for key, group_records in grouped.items():
            if isinstance(key, tuple):
                result = dict(zip(group_by, key))
            else:
                result = {group_by[0]: key}
            for field, agg_spec in aggregations.items():
                result[field] = self._apply_aggregation(group_records, agg_spec)
            results.append(result)
        return results

    def _group_records(self, records: List[dict], group_by: List[str]) -> dict:
        """Group records by specified fields."""
        grouped = {}
        for record in records:
            key = tuple(record.get(f) for f in group_by)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(record)
        return grouped

    def _apply_aggregation(self, records: List[dict], agg_spec: str) -> Any:
        """Apply aggregation function to records."""
        func_map = {
            "sum": self._sum,
            "count": self._count,
            "mean": self._mean,
            "avg": self._mean,
            "min": self._min,
            "max": self._max,
            "std": self._std,
            "first": self._first,
            "last": self._last,
            "list": self._list,
            "median": self._median,
            "mode": self._mode,
        }

        # Parse agg_spec: could be "sum,field" or just "count"
        parts = agg_spec.split(",")
        agg_func = parts[0].strip()
        agg_field = parts[1].strip() if len(parts) > 1 else None

        if agg_func in func_map:
            return func_map[agg_func](records, agg_field)
        return None

    def _sum(self, records: List[dict], field: str) -> float:
        """Sum of field values."""
        if field is None:
            return 0.0
        return sum(r.get(field, 0) or 0 for r in records)

    def _count(self, records: List[dict], field: str) -> int:
        """Number of records."""
        return len(records)

    def _mean(self, records: List[dict], field: str) -> float:
        """Mean of field values."""
        if field is None:
            return 0.0
        values = [r.get(field) for r in records if r.get(field) is not None]
        return sum(values) / len(values) if values else 0.0

    def _min(self, records: List[dict], field: str) -> Any:
        """Minimum value."""
        if field is None:
            return None
        values = [r.get(field) for r in records if field in r and r.get(field) is not None]
        return min(values) if values else None

    def _max(self, records: List[dict], field: str) -> Any:
        """Maximum value."""
        if field is None:
            return None
        values = [r.get(field) for r in records if field in r and r.get(field) is not None]
        return max(values) if values else None

    def _std(self, records: List[dict], field: str) -> float:
        """Standard deviation."""
        if field is None:
            return 0.0
        values = [r.get(field) for r in records if r.get(field) is not None]
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return variance ** 0.5

    def _first(self, records: List[dict], field: str) -> Any:
        """First value."""
        return records[0].get(field) if records and field in records[0] else None

    def _last(self, records: List[dict], field: str) -> Any:
        """Last value."""
        return records[-1].get(field) if records and field in records[-1] else None

    def _list(self, records: List[dict], field: str) -> List[Any]:
        """List of all values."""
        if field is None:
            return []
        return [r.get(field) for r in records if field in r]

    def _median(self, records: List[dict], field: str) -> float:
        """Median value."""
        if field is None:
            return 0.0
        values = sorted([r.get(field) for r in records if r.get(field) is not None])
        n = len(values)
        if n == 0:
            return 0.0
        mid = n // 2
        if n % 2 == 0:
            return (values[mid - 1] + values[mid]) / 2
        return values[mid]

    def _mode(self, records: List[dict], field: str) -> Any:
        """Most common value."""
        if field is None:
            return None
        counts = {}
        for r in records:
            val = r.get(field)
            if val is not None:
                counts[val] = counts.get(val, 0) + 1
        if not counts:
            return None
        return max(counts, key=counts.get)