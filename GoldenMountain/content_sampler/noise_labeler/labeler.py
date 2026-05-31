"""Noise labeler."""

from typing import Any
from datetime import datetime

from .detectors import (
    MissingValueDetector,
    OutlierDetector,
    FormatDetector,
    DuplicateDetector,
)


class NoiseLabeler:
    """Label noise in data records."""

    def __init__(self):
        self.labels = []
        self.missing_detector = MissingValueDetector()
        self.outlier_detector = OutlierDetector()
        self.format_detector = FormatDetector()
        self.duplicate_detector = DuplicateDetector()

    def label_record(self, record: dict, noise_type: str, field: str = None, severity: str = "low", record_index: int = None):
        """Label a specific record or field as noise."""
        self.labels.append({
            "record_id": record.get("_id"),
            "record_index": record_index,
            "field": field,
            "noise_type": noise_type,
            "severity": severity,
            "original_value": record.get(field) if field else None,
            "suggested_action": self._get_action(noise_type)
        })

    def label_field(self, field_name: str, noise_type: str, confidence: float):
        """Label entire field as noisy."""
        self.labels.append({
            "field": field_name,
            "noise_type": noise_type,
            "confidence": confidence,
            "affected_records": "all"
        })

    def detect_and_label(self, records: list[dict], field: str = None) -> dict:
        """Detect and label noise in records."""
        if not records:
            return self._empty_report()

        # Get all field names
        if field:
            fields_to_check = [field]
        else:
            fields_to_check = set()
            for record in records:
                fields_to_check.update(record.keys())
            fields_to_check = sorted(fields_to_check)

        labeled_records = []
        by_type = {}
        by_field = {}

        for field_name in fields_to_check:
            values = [record.get(field_name) for record in records]

            # Missing value detection
            missing_records = self.missing_detector.detect_field(records, field_name)
            for mr in missing_records:
                self.label_record(
                    records[mr["record_index"]],
                    "missing_value",
                    field_name,
                    "medium",
                    record_index=mr["record_index"]
                )
                labeled_records.append(mr)
                by_type.setdefault("missing_value", {"count": 0, "fields": set()})["count"] += 1
                by_type["missing_value"]["fields"].add(field_name)
                by_field.setdefault(field_name, {"count": 0})["count"] += 1

            # Outlier detection for numeric fields
            numeric_values = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
            if len(numeric_values) >= 3:
                outlier_records = self.outlier_detector.detect_field(records, field_name)
                for orec in outlier_records:
                    self.label_record(
                        records[orec["record_index"]],
                        "outlier",
                        field_name,
                        "high",
                        record_index=orec["record_index"]
                    )
                    labeled_records.append(orec)
                    by_type.setdefault("outlier", {"count": 0, "fields": set()})["count"] += 1
                    by_type["outlier"]["fields"].add(field_name)
                    by_field.setdefault(field_name, {"count": 0})["count"] += 1

            # Duplicate detection
            duplicate_records = self.duplicate_detector.detect_field(records, field_name)
            for dr in duplicate_records:
                self.label_record(
                    records[dr["record_index"]],
                    "duplicate",
                    field_name,
                    "high",
                    record_index=dr["record_index"]
                )
                labeled_records.append(dr)
                by_type.setdefault("duplicate", {"count": 0, "fields": set()})["count"] += 1
                by_type["duplicate"]["fields"].add(field_name)
                by_field.setdefault(field_name, {"count": 0})["count"] += 1

        # Convert sets to lists for JSON serialization
        for noise_type in by_type:
            by_type[noise_type]["fields"] = list(by_type[noise_type]["fields"])

        return {
            "noise_report": {
                "total_records_analyzed": len(records),
                "records_with_noise": len(labeled_records),
                "noise_rate": len(labeled_records) / len(records) if records else 0,
                "by_type": by_type,
                "by_field": by_field,
                "labeled_records": labeled_records
            }
        }

    def _empty_report(self) -> dict:
        return {
            "noise_report": {
                "total_records_analyzed": 0,
                "records_with_noise": 0,
                "noise_rate": 0,
                "by_type": {},
                "by_field": {},
                "labeled_records": []
            }
        }

    def _get_action(self, noise_type: str) -> str:
        actions = {
            "missing_value": "impute or remove",
            "outlier": "investigate or cap",
            "inconsistent_format": "standardize",
            "duplicate": "deduplicate",
            "invalid_char": "sanitize or remove",
            "type_mismatch": "convert or coerce",
            "encoding_issue": "re-encode",
            "truncation": "expand field or truncate"
        }
        return actions.get(noise_type, "review manually")

    def clean(self, records: list[dict], remove_labeled: bool = False) -> list[dict]:
        """Clean records based on labels."""
        if not remove_labeled:
            return records

        labeled_indices = set()
        for label in self.labels:
            if "record_index" in label:
                labeled_indices.add(label["record_index"])

        return [r for i, r in enumerate(records) if i not in labeled_indices]

    def get_labels(self) -> list[dict]:
        """Get all labels."""
        return self.labels

    def clear_labels(self):
        """Clear all labels."""
        self.labels = []
