# Ticket Triage - Frontend

A Next.js (App Router) + TypeScript + Tailwind CSS console for the Ticket Triage
service. It talks to the FastAPI backend over HTTP and provides:

- A ticket form (subject, body, product, customer tier) with a sample loader.
- A result view: predicted category with a confidence bar, top alternatives,
  an escalation card (probability + rationale), the grounded reply draft with a
  copy button, and the retrieved grounding sources.
- An evaluation tab that runs the offline KPI suite and renders the metrics.

## Prerequisites

- Node.js 18+ (developed on Node 22).
- The backend API running (see the root README - `make run-api`).

## Setup

```bash
cd frontend
npm install
cp .env.example .env.local   # optional; defaults to http://localhost:8000
npm run dev
```

The app runs at http://localhost:3000 and calls the API at
`NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

## Scripts

- `npm run dev` - start the dev server.
- `npm run build` - production build.
- `npm run start` - serve the production build.
- `npm run lint` - run ESLint.

## Structure

```
app/
  layout.tsx        Root layout and metadata
  page.tsx          Console: tabs, state, API wiring
  globals.css       Tailwind layers and component classes
components/
  TicketForm.tsx    Input form with sample loader
  TriageResult.tsx  Category / escalation / draft / sources
  EscalationBadge.tsx
  ConfidenceBar.tsx
  SourceList.tsx
  CopyButton.tsx
  MetricsPanel.tsx  Evaluation KPI grid
lib/
  api.ts            Typed API client with error handling
  types.ts          Shared response types
```
