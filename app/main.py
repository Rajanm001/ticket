from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import settings
from app.schemas import EvaluateResponse, HealthResponse, TicketInput, TriageResponse
from app.service import TriageService


app = FastAPI(title="Ticket Triage", version="1.0.0")

# Allow the Next.js frontend (and any configured origins) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

service = TriageService()

_INDEX_HTML = (Path(__file__).resolve().parent / "web" / "index.html").read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    """Serve the zero-dependency fallback UI (the Next.js app is the primary UI)."""
    return _INDEX_HTML


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/triage", response_model=TriageResponse)
async def triage(ticket: TicketInput) -> TriageResponse:
    ticket_id = ticket.ticket_id or "TEMP_ID"
    result = await service.triage(
        ticket_id=ticket_id,
        title=ticket.title,
        body=ticket.body,
        product=ticket.product,
        customer_tier=ticket.customer_tier,
    )
    return TriageResponse(**result)


@app.post("/evaluate", response_model=EvaluateResponse)
async def evaluate() -> EvaluateResponse:
    result = await service.evaluate()
    return EvaluateResponse(**result)
