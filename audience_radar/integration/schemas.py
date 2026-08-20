from pydantic import BaseModel, Field
from typing import List, Dict, Any

class AudienceSchema(BaseModel):
    segments: List[str]
    description: str

class ProblemSchema(BaseModel):
    statement: str
    severity: str

class AudienceLanguageSchema(BaseModel):
    phrases: List[str]
    desired_outcomes: List[str]
    avoid: List[str]

class EvidenceSchema(BaseModel):
    source_count: int
    distinct_authors: int
    platforms: Dict[str, Any]
    urls: List[str]

class LabelsSchema(BaseModel):
    observed_fact: str
    ai_interpretation: str
    hypothesis: str
    recommendation: str

class GuardrailsSchema(BaseModel):
    do_not_say: List[str]
    claims_requiring_verification: List[str]

class OpportunityV1(BaseModel):
    schema_version: str = Field(alias="schema", default="opportunity.v1")
    id: str
    title: str
    core_idea: str
    audience: AudienceSchema
    problem: ProblemSchema
    audience_language: AudienceLanguageSchema
    angle: str
    hooks: List[str]
    structure: List[str]
    cta: str
    format: str
    platforms: List[str]
    evidence: EvidenceSchema
    labels: LabelsSchema
    guardrails: GuardrailsSchema
    score: int
    confidence: float
    status: str
