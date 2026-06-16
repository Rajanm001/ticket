import type { TriageResult as TriageResultData } from "@/lib/types";
import { ConfidenceBar } from "./ConfidenceBar";
import { CopyButton } from "./CopyButton";
import { EscalationBadge } from "./EscalationBadge";
import { SourceList } from "./SourceList";

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
      {children}
    </h3>
  );
}

export function TriageResult({ result }: { result: TriageResultData }) {
  return (
    <div className="animate-fade-up space-y-5">
      <div className="card p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <SectionTitle>Predicted category</SectionTitle>
            <p className="text-2xl font-semibold text-slate-50">
              {result.category}
            </p>
          </div>
          <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 font-mono text-xs text-slate-400">
            {result.latency_ms.toFixed(1)} ms
          </span>
        </div>

        <div className="mt-4">
          <ConfidenceBar value={result.confidence} label="Confidence" />
        </div>

        {result.top_alternatives.length > 0 ? (
          <div className="mt-4">
            <SectionTitle>Top alternatives</SectionTitle>
            <div className="flex flex-wrap gap-2">
              {result.top_alternatives.map((alt) => (
                <span
                  key={alt}
                  className="rounded-full border border-white/10 bg-ink-850/70 px-3 py-1 text-xs text-slate-300"
                >
                  {alt}
                </span>
              ))}
            </div>
          </div>
        ) : null}
      </div>

      <div className="card p-5">
        <SectionTitle>Escalation prediction</SectionTitle>
        <EscalationBadge
          willEscalate={result.will_escalate}
          probability={result.escalation_probability}
          rationale={result.escalation_rationale}
        />
      </div>

      <div className="card p-5">
        <div className="mb-3 flex items-center justify-between">
          <SectionTitle>Suggested first reply</SectionTitle>
          <CopyButton text={result.draft_reply} />
        </div>
        <pre className="whitespace-pre-wrap rounded-lg border border-white/10 bg-ink-850/60 p-4 font-sans text-sm leading-relaxed text-slate-200">
          {result.draft_reply}
        </pre>
      </div>

      <div className="card p-5">
        <SectionTitle>Grounding sources</SectionTitle>
        <SourceList sources={result.sources} />
      </div>
    </div>
  );
}
