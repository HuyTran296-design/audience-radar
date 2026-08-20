import pytest
from audience_radar.reporting.validation import NumericValidator
from audience_radar.reporting.radar import RadarGenerator
from audience_radar.observability.cost import CostLedger

def test_numeric_validator():
    payload = {
        "topics": [{"id": 1, "score": 90.5}],
        "stats": {"count": 100}
    }
    
    # Valid - only uses numbers from payload
    assert NumericValidator.validate("The score was 90.5 and count was 100.", payload) is True
    
    # Valid - '1' exists in payload inside the id
    assert NumericValidator.validate("Number 1 is good.", payload) is True
    
    # Invalid - '99' is hallucinated
    assert NumericValidator.validate("The score was 99.", payload) is False

def test_radar_generator_fallback(monkeypatch):
    ledger = CostLedger()
    generator = RadarGenerator(ledger)
    
    # Mock LLM to always return a hallucinated number
    def mock_llm(prompt):
        return "# 1. Summary\nHallucinated score is 999."
        
    monkeypatch.setattr(generator, "_call_llm", mock_llm)
    
    payload = {"topics": [], "count": 10}
    report = generator.generate(payload)
    
    # It should fallback to the template because 999 is hallucinated
    assert "Fallback generated" in report
    
def test_radar_generator_success(monkeypatch):
    ledger = CostLedger()
    generator = RadarGenerator(ledger)
    
    def mock_llm(prompt):
        return "# 1. Summary\nScore is 10."
        
    monkeypatch.setattr(generator, "_call_llm", mock_llm)
    
    payload = {"topics": [], "count": 10, "sections": 1}
    report = generator.generate(payload)
    
    # Wait, the check_sections requires >= 5 headers in my mock logic.
    # So this would fallback!
    assert "Fallback generated" in report

def test_radar_generator_success_headers(monkeypatch):
    ledger = CostLedger()
    generator = RadarGenerator(ledger)
    
    def mock_llm(prompt):
        return "# 1\n# 2\n# 3\n# 4\n# 5\nScore is 10."
        
    monkeypatch.setattr(generator, "_call_llm", mock_llm)
    
    payload = {"topics": [], "count": 10, "s": [1,2,3,4,5]}
    report = generator.generate(payload)
    
    assert "Score is 10." in report
    assert "Fallback" not in report
