from __future__ import annotations

from pydantic import BaseModel, Field


class TicketInput(BaseModel):
    ticket_id: str = Field(default="")
    title: str
    body: str
    product: str | None = Field(default=None, description="Optional product area, e.g. web/api/mobile")
    customer_tier: str | None = Field(default=None, description="Optional account tier, e.g. free/pro/enterprise")


class ClassificationOutput(BaseModel):
    category: str
    confidence: float
    top_alternatives: list[str]


class EscalationOutput(BaseModel):
    will_escalate: bool
    probability: float
    rationale: str


class SourceItem(BaseModel):
    source_id: str
    source_type: str
    score: float
    snippet: str


class TriageResponse(BaseModel):
    ticket_id: str
    category: str
    confidence: float
    top_alternatives: list[str]
    will_escalate: bool
    escalation_probability: float
    escalation_rationale: str
    draft_reply: str
    sources: list[SourceItem]
    latency_ms: float


class EvaluateResponse(BaseModel):
    routing_accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    groundedness: float
    ttfr_minutes_saved: float
    cost_per_100_tickets_usd: float
    sample_size: int


class HealthResponse(BaseModel):
    status: str
