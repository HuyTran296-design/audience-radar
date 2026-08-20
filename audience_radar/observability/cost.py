from typing import Optional
from datetime import datetime
import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

class BudgetExceeded(Exception):
    pass

class CostLedger:
    def __init__(self, monthly_cap_usd: float = 30.0):
        self.monthly_cap_usd = monthly_cap_usd
        self._current_month_spend = 0.0

    def get_current_spend(self, year: int, month: int) -> float:
        # In a real implementation, this queries the database.
        # For M1, we mock the in-memory spend or return 0
        return self._current_month_spend

    def record_cost(self, agent: str, model: str, tier: str, tokens_in: int, tokens_out: int, cost_usd: float, content_id: Optional[str] = None, cache_hit: bool = False, dry_run: bool = False):
        if cache_hit:
            return

        now = datetime.utcnow()
        current_spend = self.get_current_spend(now.year, now.month)
        
        if current_spend + cost_usd > self.monthly_cap_usd:
            logger.error("budget_exceeded", cap=self.monthly_cap_usd, attempted_spend=current_spend + cost_usd)
            raise BudgetExceeded("Monthly LLM cost cap exceeded.")

        if not dry_run:
            self._current_month_spend += cost_usd
            logger.info("cost_recorded", agent=agent, cost_usd=cost_usd, total_spend=self._current_month_spend)
