"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, checkHealth, runEvaluation, triageTicket } from "@/lib/api";
import type {
  EvaluationResult,
  TriageRequest,
  TriageResult as TriageResultData,
} from "@/lib/types";
import { MetricsPanel } from "@/components/MetricsPanel";
import { TicketForm } from "@/components/TicketForm";
import { TriageResult } from "@/components/TriageResult";

type Tab = "triage" | "evaluation";

function ApiStatus() {
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let active = true;
    checkHealth()
      .then(() => active && setOnline(true))
      .catch(() => active && setOnline(false));
    return () => {
      active = false;
    };
  }, []);

  const label =
    online === null ? "Checking API" : online ? "API online" : "API offline";
  const color =
    online === null
      ? "bg-slate-400"
      : online
        ? "bg-emerald-400"
        : "bg-rose-400";

  return (
    <div className="flex items-center gap-2 text-xs text-slate-400">
      <span className={`h-2 w-2 rounded-full ${color}`} />
      {label}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="card flex h-full min-h-[20rem] flex-col items-center justify-center p-8 text-center">
      <p className="text-sm font-medium text-slate-300">No ticket triaged yet</p>
      <p className="mt-1 max-w-xs text-xs text-slate-500">
        Submit a ticket on the left to see its category, escalation risk, a
        grounded reply draft, and the sources behind it.
      </p>
    </div>
  );
}

export default function Home() {
  const [tab, setTab] = useState<Tab>("triage");
  const [result, setResult] = useState<TriageResultData | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [evalLoading, setEvalLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleTriage = useCallback(async (payload: TriageRequest) => {
    setLoading(true);
    setError(null);
    try {
      setResult(await triageTicket(payload));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }, []);

  const handleEvaluate = useCallback(async () => {
    setEvalLoading(true);
    setError(null);
    try {
      setEvaluation(await runEvaluation());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setEvalLoading(false);
    }
  }, []);

  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
      <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent-400">
            Support Operations
          </p>
          <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-50">
            Ticket Triage Console
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-slate-400">
            Classify incoming tickets, predict escalations with rationale, and
            draft grounded first replies cited to past resolutions and policy.
          </p>
        </div>
        <ApiStatus />
      </header>

      <nav className="mb-6 inline-flex rounded-lg border border-white/10 bg-ink-900/60 p-1">
        <button
          type="button"
          onClick={() => setTab("triage")}
          className={`rounded-md px-4 py-1.5 text-sm font-medium transition ${
            tab === "triage"
              ? "bg-accent-500 text-white"
              : "text-slate-300 hover:text-white"
          }`}
        >
          Triage
        </button>
        <button
          type="button"
          onClick={() => setTab("evaluation")}
          className={`rounded-md px-4 py-1.5 text-sm font-medium transition ${
            tab === "evaluation"
              ? "bg-accent-500 text-white"
              : "text-slate-300 hover:text-white"
          }`}
        >
          Evaluation
        </button>
      </nav>

      {error ? (
        <div className="mb-6 rounded-lg border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          {error}
        </div>
      ) : null}

      {tab === "triage" ? (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,24rem)_minmax(0,1fr)]">
          <div>
            <TicketForm onSubmit={handleTriage} loading={loading} />
          </div>
          <div>{result ? <TriageResult result={result} /> : <EmptyState />}</div>
        </div>
      ) : (
        <div className="space-y-5">
          <div className="card flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-100">
                Offline evaluation
              </h2>
              <p className="mt-1 text-xs text-slate-400">
                Runs the full pipeline over the historical dataset and reports
                the assignment KPIs.
              </p>
            </div>
            <button
              type="button"
              onClick={handleEvaluate}
              className="btn-ghost"
              disabled={evalLoading}
            >
              {evalLoading ? "Running..." : "Run evaluation"}
            </button>
          </div>
          {evaluation ? (
            <MetricsPanel data={evaluation} />
          ) : (
            <div className="card p-8 text-center text-sm text-slate-500">
              Run the evaluation to see routing accuracy, escalation
              precision/recall/AUC, groundedness, TTFR, and cost.
            </div>
          )}
        </div>
      )}
    </main>
  );
}
