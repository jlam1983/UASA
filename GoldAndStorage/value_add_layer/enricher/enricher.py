"""DataEnricher - Adds computed fields, lookup values, and derived data to records."""

from typing import List, Dict, Optional

from .rules import EnrichmentRule


class DataEnricher:
    """Enriches records with calculated and lookup-based fields."""

    def enrich(
        self,
        records: list[dict],
        rules: list[EnrichmentRule],
        lookup_sources: Optional[dict] = None
    ) -> list[dict]:
        """Apply enrichment rules to records."""
        for record in records:
            for rule in rules:
                record[rule.target_field] = rule.compute(record)
        return records

    def enrich_with_lookups(
        self,
        records: list[dict],
        lookup_config: dict
    ) -> list[dict]:
        """Enrich records using an external lookup source."""
        index = self._build_lookup_index(
            lookup_config["source"],
            lookup_config["key_field"]
        )
        for record in records:
            lookup_key = record.get(lookup_config["lookup_key"])
            if lookup_key in index:
                record.update(index[lookup_key])
        return records

    def _build_lookup_index(
        self,
        source: dict,
        key_field: str
    ) -> dict:
        """Build a lookup index from a source dictionary."""
        return source