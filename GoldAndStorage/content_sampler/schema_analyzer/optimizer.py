"""Schema optimization for target databases."""

from typing import Any

from .type_detector import TypeDetector
from .type_mapping import TypeMapping


class SchemaOptimizer:
    """Optimizes schema for target database."""

    def __init__(self, target: str = "sqlite"):
        self.target = target

    def optimize_field(self, field_info: dict) -> dict:
        """Optimize a single field for target database."""
        inferred_type = field_info.get("type", "string")
        max_length = field_info.get("max_length", 255)
        nullable = field_info.get("nullable", True)

        if inferred_type == "integer" and "min" in field_info and "max" in field_info:
            optimized_type = TypeMapping.optimize_integer_range(
                field_info["min"], field_info["max"], self.target
            )
        else:
            optimized_type = TypeMapping.map_type(inferred_type, self.target, max_length)

        constraints = []
        if not nullable:
            constraints.append("NOT NULL")

        if field_info.get("unique"):
            constraints.append("UNIQUE")

        return {
            "name": field_info["name"],
            "source_type": inferred_type,
            "target_type": optimized_type,
            "constraints": constraints,
            "nullable": nullable,
        }

    def optimize_schema(self, schema_analysis: dict) -> dict:
        """Optimize entire schema for target database."""
        optimized_fields = []

        for field in schema_analysis.get("fields", []):
            optimized = self.optimize_field(field)
            optimized_fields.append(optimized)

        # Generate CREATE TABLE SQL
        create_sql = self._generate_create_sql(optimized_fields, schema_analysis.get("table_name", "data"))

        return {
            "target": self.target,
            "fields": optimized_fields,
            "create_sql": create_sql,
        }

    def _generate_create_sql(self, fields: list[dict], table_name: str) -> str:
        """Generate CREATE TABLE SQL."""
        lines = [f"CREATE TABLE {table_name} ("]
        col_defs = []

        for field in fields:
            col_def = f"  {field['name']} {field['target_type']}"
            if field.get("constraints"):
                col_def += " " + " ".join(field["constraints"])
            col_defs.append(col_def)

        lines.append(",\n".join(col_defs))
        lines.append(");")

        return "\n".join(lines)

    def suggest_indexes(self, schema_analysis: dict) -> list[dict]:
        """Suggest indexes based on schema analysis."""
        indexes = []

        for field in schema_analysis.get("fields", []):
            if field.get("unique"):
                indexes.append({
                    "name": f"idx_{field['name']}",
                    "fields": [field["name"]],
                    "unique": True,
                    "reason": "Unique field"
                })
            elif field.get("cardinality_ratio", 0) > 0.9:
                indexes.append({
                    "name": f"idx_{field['name']}",
                    "fields": [field["name"]],
                    "unique": False,
                    "reason": "High cardinality"
                })

        return indexes
