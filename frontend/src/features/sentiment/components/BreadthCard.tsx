import { useMemo, useState } from "react";
import { useLanguage } from "../../../app/language";
import { Sparkline } from "../../../components/charts/Sparkline";
import { formatCompactDate, formatPercent } from "../../../lib/format";
import type { BreadthSnapshot, BreadthTrendResponse, TimeSeriesPoint } from "../types";

type BreadthCardProps = {
  snapshot: BreadthSnapshot;
  trend?: BreadthTrendResponse;
};

type BreadthPeriod = "20D" | "50D" | "200D";

const PERIODS: BreadthPeriod[] = ["20D", "50D", "200D"];

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

    return "text-slate-800 dark:text-slate-200";
};

const seriesByPeriod = (trend: BreadthTrendResponse | undefined, period: BreadthPeriod): TimeSeriesPoint[] => {
  if (!trend) {
    return [];
  }

  if (period === "20D") {
    return trend.above_20d_series;
  }
  if (period === "50D") {
    return trend.above_50d_series;
  }
  return trend.above_200d_series;
};

export function BreadthCard({ snapshot, trend }: BreadthCardProps) {
  const { isZh } = useLanguage();
  const [selectedPeriod, setSelectedPeriod] = useState<BreadthPeriod>("50D");
  const metrics = [
    { label: "20D", value: snapshot.above_20d_pct },
    { label: "50D", value: snapshot.above_50d_pct },
    { label: "200D", value: snapshot.above_200d_pct }
  ];
  const selectedSeries = useMemo(() => seriesByPeriod(trend, selectedPeriod), [trend, selectedPeriod]);

  return (
    <section className="flex h-full flex-col rounded-[28px] border border-slate-200/70 bg-white/88 p-5 shadow-panel backdrop-blur dark:border-white/10 dark:bg-slate-900/86 sm:p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-slate-500 dark:text-slate-400">{isZh ? "市场宽度" : "Market Breadth"}</p>
          <h3 className="mt-2 font-display text-xl font-semibold text-slate-950 dark:text-slate-50">{snapshot.display_name}</h3>
        </div>
        <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-500 dark:border-white/10 dark:bg-slate-950/70 dark:text-slate-400">
          {formatCompactDate(snapshot.as_of_date)}
        </div>
      </div>

      <div className="mt-5 grid grid-cols-3 gap-3">
        {metrics.map((metric) => (
          <div key={metric.label} className="rounded-2xl bg-slate-50 px-3 py-4 text-center dark:bg-slate-950/58">
            <div className="text-xs font-medium uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">{metric.label}</div>
            <div className={`metric-number mt-3 text-2xl font-semibold ${getValueClassName(metric.value)}`}>{formatPercent(metric.value, 0)}</div>
          </div>
        ))}
      </div>

      <div className="mt-auto border-t border-slate-100 pt-4 dark:border-white/10">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400 dark:text-slate-500">{isZh ? "30日走势" : "30D Timeline"}</div>
            <div className="mt-1 text-sm font-medium text-slate-600 dark:text-slate-400">
              {isZh ? `${selectedPeriod} 高于移动均线比例` : `${selectedPeriod} above moving average`}
            </div>
          </div>
          <div className="flex rounded-full border border-slate-200 bg-slate-50 p-1 dark:border-white/10 dark:bg-slate-950/70">
            {PERIODS.map((period) => (
              <button
                key={period}
                type="button"
                onClick={() => setSelectedPeriod(period)}
                className={`rounded-full px-2.5 py-1 text-xs font-semibold transition ${
                  selectedPeriod === period ? "bg-white text-blue-700 shadow-sm dark:bg-amber-400 dark:text-slate-950" : "text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
                }`}
              >
                {period}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-4">
          <Sparkline
            data={selectedSeries.map((item) => item.value)}
            labels={selectedSeries.map((item) => formatCompactDate(item.trade_date))}
            color="#0891b2"
            height={76}
          />
        </div>
      </div>
    </section>
  );
}
