# Architecture

## Overview

The service takes a raw support ticket and returns, in a single call: a category
with confidence and alternatives, an escalation decision with probability and a
human-readable rationale, and a grounded first-reply draft that cites the
evidence it relied on. Everything runs locally and deterministically by default.

## Components

1. **API layer (FastAPI)** - `app/main.py`
   - `GET /`: zero-dependency fallback web UI (static HTML served by FastAPI)
   - `POST /triage`: classify + escalate + retrieve + draft
   - `POST /evaluate`: quality metrics over the dataset
   - `GET /health`: liveness probe
   - `app/cli.py`: a command-line entry point for triaging a single ticket
     (flags or JSON in, JSON result out).
   - A separate **Next.js + React + Tailwind** console in `frontend/` is the
     primary UI; it calls the API over HTTP (CORS-enabled).

2. **Service layer** - `app/service.py`
   - `TriageService` orchestrates the flow, redacts PII on the way in, measures
     latency, and persists a minimal record of each run.

3. **Models / logic**
   - `classifier.py`: transparent weighted-keyword classifier returning
     `(category, confidence, top_alternatives)`.
   - `escalation.py`: signal-based risk model. Each matched text signal
     contributes a weight, combined with the customer tier; the rationale names
     the signals that fired (e.g. "high-value (enterprise) account").
  - `rag.py`: TF-IDF retrieval (`TfidfVectorizer` with 1-2 grams + cosine
     similarity) over past tickets and FAQ/policy entries.
   - `generator.py`: deterministic, retrieval-grounded reply template with an
     optional local-LLM rephrase that falls back automatically.
   - `evaluator.py`: real metrics via `scikit-learn` plus a groundedness and a
     time-to-first-response proxy.

4. **Data layer**
   - JSON dataset in `data/` (300 historical tickets, 15 FAQ/policy entries).
   - SQLite persistence of triage runs via `repository.py`.

5. **Security & observability**
   - `pii_guard.py` redacts emails, phone numbers, and tokens before logging.
   - Structured JSON logging via Loguru.

## Key design decisions

- **TF-IDF retrieval instead of neural embeddings.** It is deterministic, has no
  model-download or GPU dependency, returns results well under the 4-second
  budget on a laptop, and is easy to audit. This directly supports the
  reliability and low-hallucination goals; neural embeddings can be swapped in
  later behind the same `Retriever` interface without touching the API.
- **Grounded template as the default reply path.** The draft only states next
  steps that appear in retrieved snippets and always lists its source IDs, which
  keeps hallucinations near zero. When retrieval confidence is low, it asks a
  clarifying question instead of inventing an answer.
- **Optional LLM with graceful fallback.** Setting `USE_OLLAMA=true` lets a local
  model rephrase the same grounded facts; any failure falls back to the
  deterministic draft so the service never hard-depends on a model being up.
- **Privacy by default.** PII is redacted before anything is logged or stored,
  and each triage emits a structured JSON log line (input, prediction,
  confidence, escalation, source IDs, latency) on stderr.

## Request flow

1. Ticket arrives at `POST /triage`.
2. PII is sanitised.
3. Category and escalation are predicted.
4. The retriever fetches the top evidence from past tickets and FAQ/policy.
5. The generator drafts a grounded first reply with citations.
6. The response is returned and a minimal run record is stored.
