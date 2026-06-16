import type { EvaluationResult } from "@/lib/types";

interface Metric {
  label: string;
  value: string;
  hint: string;
}

function toMetrics(data: EvaluationResult): Metric[] {
  return [
    {
      label: "Routing accuracy",
      value: `${(data.routing_accuracy * 100).toFixed(1)}%`,
      hint: "Correct category share",
    },
    {
      label: "Escalation F1",
      value: data.f1.toFixed(2),
      hint: `P ${data.precision.toFixed(2)} / R ${data.recall.toFixed(2)}`,
    },
    {
      label: "Escalation ROC-AUC",
      value: data.roc_auc.toFixed(2),
      hint: "Ranking quality",
    },
    {
      label: "Groundedness",
      value: `${(data.groundedness * 100).toFixed(0)}%`,
      hint: "Claims backed by sources",
    },
    {
      label: "TTFR saved",
      value: `${data.ttfr_minutes_saved.toFixed(1)} min`,
      hint: "Per first reply",
    },
    {
      label: "Cost / 100 tickets",
      value: `$${data.cost_per_100_tickets_usd.toFixed(2)}`,
      hint: "Default offline path",
    },
  ];
}

export function MetricsPanel({ data }: { data: EvaluationResult }) {
  return (
    <div className="animate-fade-up space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {toMetrics(data).map((metric) => (
          <div key={metric.label} className="card p-5">
            <p className="text-xs uppercase tracking-wider text-slate-400">
              {metric.label}
            </p>
            <p className="mt-2 text-3xl font-semibold text-slate-50">
              {metric.value}
            </p>
            <p className="mt-1 text-xs text-slate-500">{metric.hint}</p>
          </div>
        ))}
      </div>
      <p className="text-xs text-slate-500">
        Evaluated over {data.sample_size} historical tickets from the local
        dataset.
      </p>
    </div>
  );
}
