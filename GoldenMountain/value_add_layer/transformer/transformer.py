"""DataTransformer and DataReshaper for data transformation and reshaping."""

from typing import List, Dict, Optional

from .normalizer import Normalizer
from .encoder import CategoricalEncoder


class DataTransformer:
    """Transforms data using various transformation strategies."""

    def __init__(self):
        self.normalizer = Normalizer()
        self.encoder = CategoricalEncoder()

    def transform(
        self,
        records: list[dict],
        strategy: str,
        config: Optional[dict] = None
    ) -> list[dict]:
        """Apply a transformation strategy to records."""
        strategies = {
            "normalize": self._normalize,
            "encode": self._encode_categorical,
            "reshape": self._reshape,
            "pivot": self._pivot,
            "filter": self._filter_records,
            "aggregate": self._aggregate,
            "melt": self._melt,
        }
        return strategies.get(strategy, lambda r, c: r)(records, config or {})

    def _normalize(self, records: list[dict], config: dict) -> list[dict]:
        """Scale numeric values to 0-1 range."""
        fields = config.get("fields", [])
        method = config.get("method", "min_max")
        return self.normalizer.normalize(records, fields, method)

    def _encode_categorical(self, records: list[dict], config: dict) -> list[dict]:
        """Encode categorical values as numbers."""
        field = config.get("field")
        method = config.get("method", "label")
        return self.encoder.encode(records, field, method)

    def _reshape(self, records: list[dict], config: dict) -> list[dict]:
        """Reshape data structure."""
        reshaper = DataReshaper()
        operation = config.get("operation", "pivot")
        if operation == "pivot":
            return reshaper.pivot(
                records,
                config.get("index"),
                config.get("columns"),
                config.get("values")
            )
        elif operation == "melt":
            return reshaper.melt(
                records,
                config.get("id_vars", []),
                config.get("value_vars", [])
            )
        return records

    def _pivot(self, records: list[dict], config: dict) -> list[dict]:
        """Pivot table transformation."""
        reshaper = DataReshaper()
        return reshaper.pivot(
            records,
            config.get("index"),
            config.get("columns"),
            config.get("values")
        )

    def _melt(self, records: list[dict], config: dict) -> list[dict]:
        """Unpivot: convert columns to rows."""
        reshaper = DataReshaper()
        return reshaper.melt(
            records,
            config.get("id_vars", []),
            config.get("value_vars", [])
        )

    def _filter_records(self, records: list[dict], config: dict) -> list[dict]:
        """Filter records by a condition."""
        condition = config.get("condition")
        if not condition:
            return records
        result = []
        for record in records:
            try:
                if eval(condition, {"__builtins__": {}}, record):
                    result.append(record)
            except Exception:
                pass
        return result

    def _aggregate(self, records: list[dict], config: dict) -> list[dict]:
        """Aggregate records (delegated to aggregator module)."""
        return records


class DataReshaper:
    """Reshape data structure."""

    def pivot(
        self,
        records: list[dict],
        index: str,
        columns: str,
        values: str
    ) -> list[dict]:
        """Pivot table: unique index+columns combinations become rows."""
        pivot_map = {}
        for record in records:
            idx = record.get(index)
            col = record.get(columns)
            val = record.get(values)
            if idx not in pivot_map:
                pivot_map[idx] = {index: idx}
            pivot_map[idx][col] = val
        return list(pivot_map.values())

    def melt(
        self,
        records: list[dict],
        id_vars: list[str],
        value_vars: list[str]
    ) -> list[dict]:
        """Unpivot: convert columns to rows."""
        result = []
        for record in records:
            base = {k: record[k] for k in id_vars if k in record}
            for var in value_vars:
                if var in record:
                    new_row = dict(base)
                    new_row["variable"] = var
                    new_row["value"] = record[var]
                    result.append(new_row)
        return result

    def nest(
        self,
        records: list[dict],
        group_by: str,
        nest_fields: list[str]
    ) -> list[dict]:
        """Nest specified fields under a group."""
        grouped = {}
        for record in records:
            key = record.get(group_by)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append({f: record[f] for f in nest_fields if f in record})
        return [{"key": k, "items": v} for k, v in grouped.items()]