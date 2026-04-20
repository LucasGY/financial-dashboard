import { formatCompactDate, formatPercent } from "../../../lib/format";
import type { BreadthSnapshot } from "../types";

type BreadthCardProps = {
  snapshot: BreadthSnapshot;
};

const getValueClassName = (value: number | null) => {
  if (value === null) {
    return "text-slate-400";
  }

  if (value <= 20) {
    return "text-emerald-600";
  }

  if (value >= 80) {
    return "text-rose-600";
  }

  return "text-slate-800";
};

export function BreadthCard({ snapshot }: BreadthCardProps) {
  const metrics = [
    { label: "20D", value: snapshot.above_20d_pct },
    { label: "50D", value: snapshot.above_50d_pct },
    { label: "200D", value: snapshot.above_200d_pct }
  ];

  return (
    <section className="rounded-[28px] border border-slate-200/70 bg-white/88 p-5 shadow-panel backdrop-blur sm:p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-slate-500">{snapshot.display_name}</p>
          <h3 className="mt-2 font-display text-xl font-semibold text-slate-950">Market Breadth</h3>
        </div>
        <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-500">
          {formatCompactDate(snapshot.as_of_date)}
        </div>
      </div>

      <div className="mt-5 grid grid-cols-3 gap-3">
        {metrics.map((metric) => (
          <div key={metric.label} className="rounded-2xl bg-slate-50 px-3 py-4 text-center">
            <div className="text-xs font-medium uppercase tracking-[0.2em] text-slate-400">{metric.label}</div>
            <div className={`metric-number mt-3 text-2xl font-semibold ${getValueClassName(metric.value)}`}>{formatPercent(metric.value, 0)}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
