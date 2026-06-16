# Ticket Triage

A support-ticket triage service. Given a ticket, it returns a category, an
escalation decision, and a grounded first-reply draft that cites the evidence it
used. It runs fully offline and deterministically by default: no API keys, no
model downloads, no GPU.

## What it does

For each incoming ticket the service produces, in one call:

1. **Classification** - one of 12 categories with a confidence score and the top
   alternative categories.
2. **Escalation** - a boolean decision, a probability, and a plain-language
   rationale that names the signals that triggered it (including the customer
   tier, e.g. "high-value (enterprise) account").
3. **First-reply draft** - a grounded response that cites past resolved tickets
   and policy entries by ID, uses placeholders such as `<order_id>` for details
   it does not have, and asks a clarifying question when retrieval confidence is
   low instead of guessing.

## Stack

- **FastAPI** for the HTTP API (with CORS for the frontend)
- **Next.js 16 + React 19 + TypeScript + Tailwind CSS** for the primary web UI
- **scikit-learn** TF-IDF retrieval over past tickets and FAQ/policy entries
- **SQLite** for run persistence
- **Loguru** for structured JSON logging
- Optional **Ollama** local LLM to rephrase grounded drafts (off by default)

The API also ships a zero-dependency fallback HTML page at `/`, so the service
is usable even without running the frontend. TF-IDF is used for retrieval
deliberately: it is deterministic, fast (well under the 4-second budget on a
laptop), fully offline, and easy to audit. See
[Architecture.md](Architecture.md) for the reasoning.

## Quick start

```bash
# 1. install dependencies
make setup

# 2. generate the local dataset (300 tickets, 15 FAQ/policy entries)
make generate-data

# 3. run the API
make run-api
```

Or do all three with a single command:

```bash
make run
```

On Windows (or anywhere `make` is not installed) the same single-command flow is:

```bash
python run.py
```

The API is then available at http://localhost:8000 (interactive docs at
http://localhost:8000/docs).

The API also serves a zero-dependency fallback UI at http://localhost:8000/.

## Web UI (Next.js)

The primary interface is a Next.js + React + Tailwind console in
[frontend/](frontend). It calls the API and renders the category with a
confidence bar, the escalation card with rationale, the grounded draft with a
copy button, the cited sources, and an evaluation dashboard. Requires Node.js
18+.

```bash
make frontend-setup   # cd frontend && npm install
make frontend         # cd frontend && npm run dev
```

The UI runs at http://localhost:3000 and talks to the API at
`NEXT_PUBLIC_API_URL` (default http://localhost:8000). See
[frontend/README.md](frontend/README.md) for details.

## Command line

A CLI is provided for triaging a single ticket without starting the server:

```bash
# from flags
python -m app.cli --title "Refund not received" --body "I cancelled but no refund. Urgent."

# with a customer tier (raises escalation for high-value accounts)
python -m app.cli --tier enterprise --title "Outage" --body "Production is down with 503s."

# from a JSON file or stdin
python -m app.cli --json ticket.json
echo '{"title":"Bug","body":"App crashes on upload"}' | python -m app.cli --json -
```

It prints the full triage result (category, escalation, grounded draft, sources)
as JSON on stdout; logs go to stderr so the output stays machine-readable.

## API

### `GET /`

The zero-dependency fallback web UI (the Next.js app is the primary UI).

### `GET /health`

```bash
curl http://localhost:8000/health
```

### `POST /triage`

```bash
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d '{"ticket_id":"CASE_1","title":"Refund not received","body":"I cancelled my plan but the refund has not arrived. This is urgent.","product":"web","customer_tier":"enterprise"}'
```

`product` and `customer_tier` are optional. Customer tier feeds the escalation
model, so an enterprise/VIP account with a risk signal is more likely to be
flagged.

Response (abridged):

```json
{
  "ticket_id": "CASE_1",
  "category": "Refund",
  "confidence": 0.6,
  "top_alternatives": ["Subscription", "Other"],
  "will_escalate": false,
  "escalation_probability": 0.25,
  "escalation_rationale": "Escalation signals detected: urgent",
  "draft_reply": "Hi, thanks for contacting support about your refund request...\n\nSources:\n- CASE_230 (ticket, relevance 0.65)",
  "sources": [{ "source_id": "CASE_230", "source_type": "ticket", "score": 0.65, "snippet": "..." }],
  "latency_ms": 12.4
}
```

### `POST /evaluate`

Runs the evaluation over the local dataset and returns routing accuracy,
escalation precision/recall/F1/ROC-AUC, groundedness, a time-to-first-response
proxy, and the estimated cost per 100 tickets. See [Results.md](Results.md) for
the current numbers and how each is computed.

## Configuration

All settings have safe defaults and can be overridden via environment variables
(see [.env.example](.env.example)):

| Variable | Default | Purpose |
| --- | --- | --- |
| `USE_OLLAMA` | `false` | Enable the optional local LLM rephrase |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | `mistral` | Ollama model name |
| `RETRIEVAL_TOP_K` | `4` | Evidence items retrieved per ticket |
| `LOW_CONFIDENCE_THRESHOLD` | `0.12` | Below this top retrieval score the draft asks for clarification |
| `COST_PER_1K_INPUT` / `COST_PER_1K_OUTPUT` | `0.0` | Token prices for the cost estimate |

When `USE_OLLAMA=true`, the LLM only rephrases facts that are already grounded in
retrieved evidence, and any failure falls back to the deterministic draft, so the
service never hard-depends on a model being available.

## Data

- `data/tickets.json` - 300 historical tickets with title, body, category,
  customer tier, product, resolution notes, and an escalation label.
- `data/faq.json` - 15 FAQ/policy entries.

Regenerate both deterministically with `make generate-data`
(`scripts/generate_data.py`, fixed seed).

## Privacy and logging

Emails, phone numbers, and tokens are redacted (`app/pii_guard.py`) before
anything is logged or persisted. Each triage emits a structured JSON log line on
stderr with the redacted input, predicted category and confidence, escalation
decision and probability, cited source IDs, and latency.

## Tests

```bash
make test
```

The suite covers the classifier, escalation model, retriever, generator
(grounded and low-confidence paths), PII redaction, the evaluator, and a
full-pipeline integration test. Everything runs offline.

## Docker

```bash
docker compose up --build
```

This builds the dataset into the image and serves the API and web UI on port
8000.

## Project layout

```
app/
  main.py          FastAPI app, routes, and web UI
  cli.py           Command-line triage tool
  service.py       Triage orchestration, PII redaction, persistence
  classifier.py    Weighted-keyword category classifier
  escalation.py    Signal-based escalation model
  rag.py           TF-IDF retriever over tickets + FAQ
  generator.py     Grounded reply template (+ optional Ollama)
  evaluator.py     scikit-learn metrics + groundedness/TTFR proxies
  data_loader.py   Dataset loading
  repository.py    SQLite persistence
  pii_guard.py     Email/phone/token redaction
  schemas.py       Pydantic request/response models
  constants.py     Category definitions
  config.py        Settings
  logging_utils.py Structured logging
  web/index.html   Zero-dependency fallback UI
frontend/                  Next.js + React + Tailwind console (primary UI)
scripts/generate_data.py   Deterministic dataset generator
tests/                     Test suite
data/                      tickets.json, faq.json
Architecture.md            Design and decisions
Results.md                 Evaluation results
```
