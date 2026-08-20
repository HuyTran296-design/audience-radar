import structlog
from typing import Dict, Any

from audience_radar.integration.schemas import OpportunityV1

logger = structlog.get_logger(__name__)

class ContentEngineExporter:
    """
    Handles safe exportation of opportunities to the external Content Engine.
    Enforces strict preconditions on the data.
    """
    
    @staticmethod
    def export(opportunity_data: Dict[str, Any], blocked: bool = False, evidence_integrity: float = 1.0) -> OpportunityV1:
        # 1. Enforce blocked status
        if blocked:
            logger.warning("export_rejected_blocked", opp_id=opportunity_data.get("id"))
            raise ValueError("Cannot export: Opportunity is blocked.")
            
        # 2. Enforce evidence integrity
        if evidence_integrity < 1.0:
            logger.warning("export_rejected_evidence", opp_id=opportunity_data.get("id"))
            raise ValueError("Cannot export: Evidence integrity must be 100%.")
            
        # 3. Enforce guardrails presence
        guardrails = opportunity_data.get("guardrails", {})
        if not guardrails or not isinstance(guardrails.get("do_not_say"), list):
            logger.warning("export_rejected_guardrails", opp_id=opportunity_data.get("id"))
            raise ValueError("Cannot export: Guardrails must be attached.")
            
        # 4. Enforce status
        if opportunity_data.get("status") != "trusted":
            logger.warning("export_rejected_status", opp_id=opportunity_data.get("id"))
            raise ValueError("Cannot export: Status must be 'trusted'.")
            
        # Validate schema exactly
        validated_opp = OpportunityV1(**opportunity_data)
        
        logger.info("export_successful", opp_id=validated_opp.id)
        return validated_opp
