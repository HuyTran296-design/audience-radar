from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict, Any, Literal

class CollectionConfig(BaseModel):
    method: Literal["api", "rss", "search", "manual", "oauth"] = "api"
    frequency: Literal["hourly", "every_6h", "daily", "every_2d", "weekly", "manual"] = "daily"
    max_items_per_run: int = 100

class AudienceConfig(BaseModel):
    description: Optional[str] = None
    target_segments: List[str] = []
    target_topics: List[str] = []

class FilterConfig(BaseModel):
    include_keywords: List[str] = []
    exclude_keywords: List[str] = []
    minimum_relevance_score: int = Field(50, ge=0, le=100)

class AnalysisConfig(BaseModel):
    collect_comments: bool = True
    extract_pain_points: bool = True
    extract_questions: bool = True
    extract_objections: bool = True
    extract_language: bool = True
    detect_trends: bool = True
    detect_purchase_intent: bool = True

class RetentionConfig(BaseModel):
    raw_data_days: int = 30
    processed_data_days: int = 90

class SourceConfig(BaseModel):
    id: str = Field(..., pattern=r"^[a-z0-9_]{3,48}$")
    name: str
    platform: str
    tier: Literal[1, 2, 3, 4] = 4
    type: str = "social"
    enabled: bool = True
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    
    collection: CollectionConfig = Field(default_factory=CollectionConfig)
    audience: AudienceConfig = Field(default_factory=AudienceConfig)
    filters: FilterConfig = Field(default_factory=FilterConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    retention: RetentionConfig = Field(default_factory=RetentionConfig)
    
    # Platform specific unstructured options
    options: Dict[str, Any] = {}

class AudienceProfile(BaseModel):
    id: str = Field(..., pattern=r"^[a-z0-9_]{3,48}$")
    name: str
    description: str
    goals: List[str]
    not_our_audience: List[str]
    segments: List[str] = []
    languages: List[str] = ["en"]
    primary_countries: List[str] = []

class WorkspaceConfig(BaseModel):
    version: int
    audience: AudienceProfile
    sources: List[SourceConfig]

