import json
from typing import List, Dict, Any
from audience_radar.storage.models import Signal, SearchSignal, Opportunity

class CrossSourceCorrelator:
    """
    Engine to correlate Search Demand Signals with Social/Review Pain Points.
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.system_prompt = """
You are a master Audience Intelligence Analyst.
I will give you a list of Search Demand keywords (from Apple Ads) and Audience Pain Points (from Reddit, App Store Reviews).
Find strong correlations where what people are searching for matches what they are complaining about.

Output JSON:
{
  "correlations": [
    {
      "core_idea": "Users want a simpler meditation experience",
      "search_demand": ["meditation timer", "simple meditation timer"],
      "audience_pain": ["Too many features", "Just want a simple timer"],
      "confidence": 0.95
    }
  ]
}
"""

    def correlate(self, search_signals: List[SearchSignal], pain_signals: List[Signal]) -> List[Opportunity]:
        if not search_signals or not pain_signals:
            return []
            
        # Build prompt corpus
        search_corpus = "\n".join([f"- {s.keyword} (Popularity: {s.search_popularity})" for s in search_signals if s.keyword])
        pain_corpus = "\n".join([f"- {s.content} (Confidence: {s.confidence})" for s in pain_signals if s.content])
        
        corpus = f"SEARCH DEMAND:\n{search_corpus}\n\nAUDIENCE PAIN:\n{pain_corpus}"
        
        try:
            # Mock LLM response for architecture completeness
            data = {
                "correlations": [
                    {
                        "core_idea": "Users want a simpler meditation experience without gamification",
                        "search_demand": ["simple meditation timer", "meditation timer no ads"],
                        "audience_pain": ["Too many streaks and badges", "I just want to close my eyes and track time"],
                        "confidence": 0.92
                    }
                ]
            }
            
            opportunities = []
            for corr in data.get("correlations", []):
                opportunities.append(Opportunity(
                    id="mock_opp_id",
                    audience_id="mock_audience",
                    title=corr["core_idea"],
                    core_idea=corr["core_idea"],
                    opportunity_class="content",
                    status="candidate",
                    opportunity_score=85,
                    score_band="High",
                    evidence_json=json.dumps({
                        "search_demand": corr["search_demand"],
                        "audience_pain": corr["audience_pain"]
                    })
                ))
            return opportunities
            
        except Exception as e:
            print(f"CrossSourceCorrelator error: {e}")
            return []
