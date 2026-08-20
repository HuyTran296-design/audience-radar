import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from audience_radar.config.models import AudienceProfile, SourceConfig
from audience_radar.observability.cost import CostLedger

@dataclass
class RelevanceResult:
    is_relevant: bool
    score: int
    intent: Optional[str]
    confidence: float
    reason: str
    tokens_in: int
    tokens_out: int
    cost_usd: float

class RelevanceScorer:
    def __init__(self, ledger: CostLedger, model: str = "gpt-4o-mini", tier: str = "cheap"):
        self.ledger = ledger
        self.model = model
        self.tier = tier
        
        # Base pricing for mock/testing
        self.cost_per_1k_in = 0.00015
        self.cost_per_1k_out = 0.0006

    def score(self, content_text: str, audience: AudienceProfile, config: SourceConfig) -> RelevanceResult:
        # Construct the prompt (not physically sending to LLM unless implemented, MVP asks for safe LLM usage)
        prompt = self._build_prompt(content_text, audience)
        
        # Estimate tokens (mock)
        tokens_in = len(prompt.split()) * 1.5
        tokens_out = 150 # Estimated JSON output
        estimated_cost = (tokens_in / 1000 * self.cost_per_1k_in) + (tokens_out / 1000 * self.cost_per_1k_out)
        
        # Pre-flight check (will raise if budget exceeded)
        self.ledger.record_cost(
            agent="relevance_scorer", model=self.model, tier=self.tier,
            tokens_in=int(tokens_in), tokens_out=tokens_out, cost_usd=estimated_cost,
            dry_run=True
        )
        
        # Call LLM
        llm_response = self._call_llm(prompt)
        
        # Parse Response
        try:
            parsed = json.loads(llm_response["content"])
            score = parsed.get("relevance_score", 0)
            min_score = config.min_relevance_score or 50
            
            result = RelevanceResult(
                is_relevant=score >= min_score,
                score=score,
                intent=parsed.get("intent"),
                confidence=parsed.get("intent_confidence", 0.0),
                reason=parsed.get("relevance_reason", ""),
                tokens_in=llm_response["usage"]["prompt_tokens"],
                tokens_out=llm_response["usage"]["completion_tokens"],
                cost_usd=estimated_cost # In reality computed from actual usage
            )
            
            # Record actual cost
            self.ledger.record_cost(
                agent="relevance_scorer", model=self.model, tier=self.tier,
                tokens_in=result.tokens_in, tokens_out=result.tokens_out, 
                cost_usd=result.cost_usd, dry_run=False
            )
            return result
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to parse LLM response schema: {str(e)}")
            
    def _build_prompt(self, text: str, audience: AudienceProfile) -> str:
        return f"Evaluate if this text is relevant to {audience.name}:\n\n{text}"
        
    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """
        Mock implementation for LLM call. In tests, we patch this. 
        In MVP, we can leave this as a mock or use an actual client.
        """
        return {
            "content": json.dumps({
                "relevance_score": 85,
                "relevance_stage": "pass",
                "relevance_reason": "Matches target audience.",
                "intent": "seeking_advice",
                "intent_confidence": 0.9,
                "is_rhetorical": False
            }),
            "usage": {
                "prompt_tokens": len(prompt.split()) * 1.5,
                "completion_tokens": 50
            }
        }
