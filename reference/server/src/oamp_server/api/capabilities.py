"""Capabilities discovery endpoint for optional OAMP features."""

from __future__ import annotations

from fastapi import APIRouter, Request


router = APIRouter(tags=["Capabilities"])


@router.get("/capabilities")
async def get_capabilities(request: Request) -> dict[str, object]:
    """Advertise optional OAMP capabilities supported by the reference backend."""
    settings = request.app.state.settings
    return {
        "oamp_version": "1.3.0",
        "capabilities": {
            "streaming": {
                "supported": False,
                "filter_keys": ["user_id", "event_type", "sensitivity_class", "governance_label"],
            },
            "as_of": {
                "supported": False,
            },
            "governance": {
                "supported": True,
                "sensitivity_classes": ["public", "internal", "confidential", "restricted"],
                "labels_supported": True,
                "extended_provenance_supported": True,
                "withheld_stub_support": False,
                "enforcement": {
                    "supported": settings.governance_enforcement_enabled,
                    "spec_version": "1.3.0",
                    "label_hierarchy": "dotted-prefix",
                    "reserved_top_level_labels": [
                        "identity",
                        "location",
                        "health",
                        "finance",
                        "relationships",
                        "work",
                        "preferences",
                        "creative",
                        "beliefs",
                        "behaviour",
                    ],
                    "grant_transport": ["jwt-claims", "oamp-grant-header"],
                    "existence_hiding": True,
                    "stream_filtering": False,
                    "export_full_supported": True,
                },
            },
            "user_id_format": {
                "description": "opaque string",
            },
            "id_preservation": "preserved",
            "content_types": ["application/json"],
            "auth_schemes": ["Bearer", "OAMP-Grant"],
        },
    }
