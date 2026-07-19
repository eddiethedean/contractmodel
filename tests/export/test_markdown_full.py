"""Tests for enriched markdown export."""

from contractmodel.core.ccm import CanonicalContract
from contractmodel.export.markdown import export_markdown
from contractmodel.export.odcs import export_odcs


def test_export_markdown_full_sections() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "full",
            "name": "Full Contract",
            "version": "1.0.0",
            "description": "A complete contract.",
            "ownership": {"owner": "data-team", "team": "platform"},
            "schema": {
                "primary_key": ["id"],
                "fields": [
                    {
                        "name": "id",
                        "logical_type": "string",
                        "required": True,
                        "description": "Identifier",
                        "constraints": {"unique": True, "min_length": 1},
                    },
                    {
                        "name": "address",
                        "logical_type": "object",
                        "children": [
                            {"name": "city", "logical_type": "string", "description": "City|Name"},
                        ],
                    },
                ],
            },
            "quality": {
                "rules": [{"name": "freshness", "type": "freshness", "threshold": 24}]
            },
            "semantics": {"namespaces": {"ex": "http://example.org/"}},
        }
    )
    md = export_markdown(contract)
    assert "## Ownership" in md
    assert "**Primary key**" in md
    assert "## Quality Rules" in md
    assert "## Semantic Namespaces" in md
    assert "City\\|Name" in md
    assert "unique" in md
    assert "address children" in md


def test_export_odcs_wrapper() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "wrap",
            "name": "Wrap",
            "version": "1.0.0",
            "schema": {"fields": [{"name": "id", "logical_type": "string"}]},
        }
    )
    odcs = export_odcs(contract)
    assert odcs["id"] == "wrap"
    assert odcs["schema"][0]["name"] == "wrap"
    assert odcs["schema"][0]["properties"][0]["name"] == "id"
