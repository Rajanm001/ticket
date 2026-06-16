import { ConfidenceBar } from "./ConfidenceBar";

interface EscalationBadgeProps {
  willEscalate: boolean;
  probability: number;
  rationale: string;
}

export function EscalationBadge({
  willEscalate,
  probability,
  rationale,
}: EscalationBadgeProps) {
  return (
    <div
      className={`rounded-xl border p-4 ${
        willEscalate
          ? "border-rose-500/40 bg-rose-500/10"
          : "border-emerald-500/30 bg-emerald-500/10"
      }`}
    >
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            className={`inline-block h-2.5 w-2.5 rounded-full ${
              willEscalate ? "bg-rose-400" : "bg-emerald-400"
            }`}
          />
          <span className="text-sm font-semibold text-slate-100">
            {willEscalate ? "Likely to escalate" : "Unlikely to escalate"}
          </span>
        </div>
        <span className="font-mono text-sm text-slate-300">
          {Math.round(probability * 100)}%
        </span>
      </div>
      <ConfidenceBar
        value={probability}
        tone={willEscalate ? "rose" : "emerald"}
      />
      <p className="mt-3 text-sm leading-relaxed text-slate-300">{rationale}</p>
    </div>
  );
}
