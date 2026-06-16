interface ConfidenceBarProps {
  value: number;
  label?: string;
  tone?: "accent" | "amber" | "rose" | "emerald";
}

const TONES: Record<NonNullable<ConfidenceBarProps["tone"]>, string> = {
  accent: "from-accent-500 to-accent-400",
  amber: "from-amber-500 to-amber-400",
  rose: "from-rose-500 to-rose-400",
  emerald: "from-emerald-500 to-emerald-400",
};

export function ConfidenceBar({ value, label, tone = "accent" }: ConfidenceBarProps) {
  const pct = Math.max(0, Math.min(100, Math.round(value * 100)));
  return (
    <div>
      {label ? (
        <div className="mb-1 flex items-center justify-between text-xs text-slate-400">
          <span>{label}</span>
          <span className="font-mono text-slate-300">{pct}%</span>
        </div>
      ) : null}
      <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
        <div
          className={`h-full animate-bar-grow rounded-full bg-gradient-to-r ${TONES[tone]}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
