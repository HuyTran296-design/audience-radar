import pytest
import json
from audience_radar.integration.content_engine import ContentEngineExporter

def get_valid_payload():
    return {
        "schema": "opportunity.v1",
        "id": "opp_123",
        "title": "Test Title",
        "core_idea": "Idea",
        "audience": {"segments": ["a"], "description": "desc"},
        "problem": {"statement": "prob", "severity": "high"},
        "audience_language": {"phrases": [], "desired_outcomes": [], "avoid": []},
        "angle": "angle",
        "hooks": [],
        "structure": [],
        "cta": "cta",
        "format": "video",
        "platforms": [],
        "evidence": {"source_count": 10, "distinct_authors": 5, "platforms": {}, "urls": []},
        "labels": {
            "observed_fact": "fact",
            "ai_interpretation": "interp",
            "hypothesis": "hypo",
            "recommendation": "rec"
        },
        "guardrails": {"do_not_say": ["bad word"], "claims_requiring_verification": []},
        "score": 90,
        "confidence": 0.85,
        "status": "trusted"
    }

def test_export_success():
    payload = get_valid_payload()
    result = ContentEngineExporter.export(payload, blocked=False, evidence_integrity=1.0)
    assert result.id == "opp_123"
    # Note Pydantic allows schema_version in object via field alias
    assert result.schema_version == "opportunity.v1"
    
def test_export_blocked():
    payload = get_valid_payload()
    with pytest.raises(ValueError, match="blocked"):
        ContentEngineExporter.export(payload, blocked=True, evidence_integrity=1.0)
        
def test_export_evidence_integrity():
    payload = get_valid_payload()
    with pytest.raises(ValueError, match="Evidence integrity"):
        ContentEngineExporter.export(payload, blocked=False, evidence_integrity=0.9)
        
def test_export_missing_guardrails():
    payload = get_valid_payload()
    payload["guardrails"] = {}
    with pytest.raises(ValueError, match="Guardrails"):
        ContentEngineExporter.export(payload, blocked=False, evidence_integrity=1.0)

def test_export_untrusted_status():
    payload = get_valid_payload()
    payload["status"] = "reviewed"
    with pytest.raises(ValueError, match="trusted"):
        ContentEngineExporter.export(payload, blocked=False, evidence_integrity=1.0)

def test_schema_parsing_failure():
    payload = get_valid_payload()
    payload.pop("core_idea") # missing required field
    
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ContentEngineExporter.export(payload, blocked=False, evidence_integrity=1.0)
