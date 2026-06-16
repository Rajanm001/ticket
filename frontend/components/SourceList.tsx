import type { Source } from "@/lib/types";

export function SourceList({ sources }: { sources: Source[] }) {
  if (sources.length === 0) {
    return (
      <p className="text-sm text-slate-400">
        No supporting sources were retrieved with sufficient confidence.
      </p>
    );
  }

  return (
    <ul className="space-y-2.5">
      {sources.map((source) => (
        <li
          key={source.source_id}
          className="rounded-lg border border-white/10 bg-ink-850/60 p-3"
        >
          <div className="mb-1.5 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="rounded bg-accent-500/15 px-1.5 py-0.5 font-mono text-xs text-accent-400">
                {source.source_id}
              </span>
              <span className="text-xs uppercase tracking-wide text-slate-500">
                {source.source_type}
              </span>
            </div>
            <span className="font-mono text-xs text-slate-400">
              {(source.score * 100).toFixed(0)}% match
            </span>
          </div>
          <p className="line-clamp-2 text-sm text-slate-300">{source.snippet}</p>
        </li>
      ))}
    </ul>
  );
}
