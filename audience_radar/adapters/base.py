from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from audience_radar.config.models import SourceConfig
from datetime import datetime

@dataclass
class FetchedItem:
    platform_item_id: str
    raw_data: dict
    fetched_at: datetime
    expires_at: datetime

@dataclass
class FetchResult:
    items: List[FetchedItem]
    next_cursor: Optional[str]
    api_calls_made: int
    quota_units_used: int

class AdapterException(Exception):
    def __init__(self, error_class: str, detail: str, retry_after: Optional[int] = None):
        self.error_class = error_class
        self.detail = detail
        self.retry_after = retry_after
        super().__init__(f"{error_class}: {detail}")

class BaseAdapter(ABC):
    def __init__(self, config: SourceConfig, db_source: Any = None):
        self.config = config
        self.db_source = db_source

    @abstractmethod
    def collect(self) -> List[Any]:
        pass

    @abstractmethod
    def normalize(self, raw_data: List[Any]) -> List[Any]:
        pass

    @abstractmethod
    def validate(self, normalized_data: List[Any]) -> List[Any]:
        pass
        
    @abstractmethod
    def deduplicate(self, validated_data: List[Any]) -> List[Any]:
        pass

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "platform": self.config.platform,
            "tier": getattr(self.config, "tier", 4),
            "source_id": self.config.id
        }

    def handle_rate_limit(self, retry_after: int):
        pass

    def handle_error(self, error: Exception):
        pass
