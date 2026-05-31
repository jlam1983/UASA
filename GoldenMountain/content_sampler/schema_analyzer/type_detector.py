"""Type detector for schema analysis."""

import re
from datetime import datetime
from typing import Any


class TypeDetector:
    """Detects and infers types from data values."""

    EMAIL_PATTERN = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
    URL_PATTERN = re.compile(r"^https?://[\w\.-]+")
    PHONE_PATTERN = re.compile(r"^[\d\s\-\+\(\)]+$")
    UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
    IPV4_PATTERN = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")

    @classmethod
    def infer_field_type(cls, values: list[Any]) -> dict:
        """Infer type information from field values."""
        non_null = [v for v in values if v is not None and v != ""]

        if not non_null:
            return {
                "type": "null",
                "nullable": True,
                "min_length": 0,
                "max_length": 0,
            }

        # Check type consistency
        types_present = set()
        for v in non_null:
            types_present.add(type(v).__name__)

        # Infer actual type
        inferred_type = cls._infer_type(non_null)

        result = {
            "type": inferred_type,
            "nullable": len(non_null) < len(values),
        }

        # Add type-specific info
        if inferred_type == "integer":
            int_vals = [int(v) for v in non_null if cls._is_integer(v)]
            if int_vals:
                result["min"] = min(int_vals)
                result["max"] = max(int_vals)

        elif inferred_type == "float":
            float_vals = [float(v) for v in non_null if cls._is_numeric(v)]
            if float_vals:
                result["min"] = min(float_vals)
                result["max"] = max(float_vals)

        elif inferred_type == "string":
            str_vals = [str(v) for v in non_null]
            result["min_length"] = min(len(s) for s in str_vals)
            result["max_length"] = max(len(s) for s in str_vals)

            # Detect special patterns
            if all(cls.EMAIL_PATTERN.match(str(v)) for v in non_null):
                result["pattern"] = "email"
            elif all(cls.URL_PATTERN.match(str(v)) for v in non_null):
                result["pattern"] = "url"
            elif all(cls.PHONE_PATTERN.match(str(v)) for v in non_null):
                result["pattern"] = "phone"
            elif all(cls.UUID_PATTERN.match(str(v)) for v in non_null):
                result["pattern"] = "uuid"
            elif all(cls.IPV4_PATTERN.match(str(v)) for v in non_null):
                result["pattern"] = "ipv4"

        elif inferred_type == "datetime":
            dt_vals = [v for v in non_null if cls._is_datetime(v)]
            if dt_vals:
                result["min"] = min(dt_vals)
                result["max"] = max(dt_vals)

        return result

    @classmethod
    def _infer_type(cls, values: list[Any]) -> str:
        """Infer the actual type of values."""
        # Check for boolean
        if all(cls._is_boolean(v) for v in values):
            return "boolean"

        # Check for integer
        if all(cls._is_integer(v) for v in values):
            return "integer"

        # Check for float/numeric
        if all(cls._is_numeric(v) for v in values):
            return "float"

        # Check for datetime
        if all(cls._is_datetime(v) for v in values):
            return "datetime"

        # Check for date
        if all(cls._is_date(v) for v in values):
            return "date"

        # Check for time
        if all(cls._is_time(v) for v in values):
            return "time"

        # Check for array
        if all(isinstance(v, list) for v in values):
            return "array"

        # Check for object/dict
        if all(isinstance(v, dict) for v in values):
            return "object"

        return "string"

    @classmethod
    def _is_boolean(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return True
        if isinstance(v, str) and v.lower() in ("true", "false", "yes", "no", "1", "0"):
            return True
        return False

    @classmethod
    def _is_integer(cls, v: Any) -> bool:
        if isinstance(v, int) and not isinstance(v, bool):
            return True
        if isinstance(v, str):
            try:
                int(v)
                return "." not in v
            except ValueError:
                return False
        return False

    @classmethod
    def _is_numeric(cls, v: Any) -> bool:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return True
        if isinstance(v, str):
            try:
                float(v)
                return True
            except ValueError:
                return False
        return False

    @classmethod
    def _is_datetime(cls, v: Any) -> bool:
        if isinstance(v, datetime):
            return True
        if isinstance(v, str):
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    datetime.strptime(v, fmt)
                    return True
                except ValueError:
                    continue
        return False

    @classmethod
    def _is_date(cls, v: Any) -> bool:
        if isinstance(v, str):
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
                try:
                    datetime.strptime(v, fmt)
                    return True
                except ValueError:
                    continue
        return False

    @classmethod
    def _is_time(cls, v: Any) -> bool:
        if isinstance(v, str):
            for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p"):
                try:
                    datetime.strptime(v, fmt)
                    return True
                except ValueError:
                    continue
        return False
