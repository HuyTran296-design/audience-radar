import json
from typing import List, Dict, Any
from dataclasses import dataclass
from audience_radar.config.models import AudienceProfile
from audience_radar.observability.cost import CostLedger
from audience_radar.storage.models import Conversation

@dataclass
class InsightResult:
    topics: List[Dict[str, Any]]
    pain_points: List[Dict[str, Any]]
    tokens_in: int
    tokens_out: int
    cost_usd: float

class InsightGenerator:
    def __init__(self, ledger: CostLedger, model: str = "gpt-4o", tier: str = "expensive"):
        self.ledger = ledger
        self.model = model
        self.tier = tier
        
        # Base pricing for mock/testing
        self.cost_per_1k_in = 0.005
        self.cost_per_1k_out = 0.015

    def generate(self, conversations: List[Conversation], audience: AudienceProfile) -> InsightResult:
        prompt = self._build_prompt(conversations, audience)
        
        tokens_in = len(prompt.split()) * 1.5
        tokens_out = 500 # Estimated JSON output
        estimated_cost = (tokens_in / 1000 * self.cost_per_1k_in) + (tokens_out / 1000 * self.cost_per_1k_out)
        
        # Pre-flight check
        self.ledger.record_cost(
            agent="insight_generator", model=self.model, tier=self.tier,
            tokens_in=int(tokens_in), tokens_out=tokens_out, cost_usd=estimated_cost,
            dry_run=True
        )
        
        llm_response = self._call_llm(prompt)
        
        try:
            parsed = json.loads(llm_response["content"])
            result = InsightResult(
                topics=parsed.get("topics", []),
                pain_points=parsed.get("pain_points", []),
                tokens_in=llm_response["usage"]["prompt_tokens"],
                tokens_out=llm_response["usage"]["completion_tokens"],
                cost_usd=estimated_cost
            )
            
            # Record actual cost
            self.ledger.record_cost(
                agent="insight_generator", model=self.model, tier=self.tier,
                tokens_in=result.tokens_in, tokens_out=result.tokens_out, 
                cost_usd=result.cost_usd, dry_run=False
            )
            return result
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to parse LLM insight schema: {str(e)}")
            
    def _build_prompt(self, conversations: List[Conversation], audience: AudienceProfile) -> str:
        texts = "\n\n".join([f"Item {c.id}:\n{c.title}\n{c.body}" for c in conversations])
        return f"Extract themes for {audience.name} from these items:\n\n{texts}"
        
    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """Mock implementation"""
        return {
            "content": json.dumps({
                "topics": [
                    {
                        "label": "Consistency struggle",
                        "description": "Users struggle to maintain a daily habit"
                    }
                ],
                "pain_points": [
                    {
                        "title": "Forgetting to meditate in the morning",
                        "severity_score": 90,
                        "topic_label": "Consistency struggle"
                    }
                ]
            }),
            "usage": {
                "prompt_tokens": len(prompt.split()) * 1.5,
                "completion_tokens": 150
            }
        }
