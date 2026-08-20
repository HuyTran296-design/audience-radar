import re
import structlog
from typing import Dict, Any, List

logger = structlog.get_logger(__name__)

class NumericValidator:
    @staticmethod
    def extract_numerals(text: str) -> List[str]:
        # Extract all distinct numerals (digits, floats, commas)
        # We look for \b\d+(?:[,.]\d+)?\b
        matches = re.findall(r'\b\d+(?:[.,]\d+)?\b', text)
        return [m.replace(",", "") for m in matches]
        
    @staticmethod
    def extract_payload_numerals(payload: Dict[str, Any]) -> set:
        numerals = set()
        
        def _walk(node):
            if isinstance(node, dict):
                for v in node.values():
                    _walk(v)
            elif isinstance(node, list):
                for v in node:
                    _walk(v)
            elif isinstance(node, (int, float)):
                numerals.add(str(node))
            elif isinstance(node, str):
                # If a string contains numbers (like an ID), we extract those too
                # so we don't accidentally fail on an ID output
                for m in re.findall(r'\b\d+(?:[.,]\d+)?\b', node):
                    numerals.add(m.replace(",", ""))
                    
        _walk(payload)
        return numerals

    @classmethod
    def validate(cls, text: str, payload: Dict[str, Any]) -> bool:
        """
        Returns True if ALL numerals found in `text` exist within `payload`.
        """
        text_numerals = set(cls.extract_numerals(text))
        payload_numerals = cls.extract_payload_numerals(payload)
        
        # Are there any numerals in the text that are NOT in the payload?
        hallucinations = text_numerals - payload_numerals
        
        # We might want to ignore numbers like '10' (for 10 sections) or '1' (for points)
        # But per the strict acceptance criteria, ANY numeral must exist in the payload.
        if hallucinations:
            logger.warning("numeric_hallucination_detected", fake_numbers=list(hallucinations))
            return False
            
        return True
