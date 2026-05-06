import { GaugeChart } from "../../../components/charts/GaugeChart";
import { Sparkline } from "../../../components/charts/Sparkline";
import { formatCompactDate, formatNumber } from "../../../lib/format";
import type { FearGreedSnapshot, FearGreedTrendResponse } from "../types";

type FearGreedCardProps = {
  snapshot: FearGreedSnapshot;
  trend: FearGreedTrendResponse;
};

const COLOR_MAP: Record<string, string> = {
  dark_green: "#166534",
  green: "#22c55e",
  neutral: "#f59e0b",
  orange: "#f97316",
  red: "#dc2626"
};

export function FearGreedCard({ snapshot, trend }: FearGreedCardProps) {
  const color = snapshot.color ? COLOR_MAP[snapshot.color] ?? "#22c55e" : "#22c55e";

  return (
    <section className="flex h-full flex-col rounded-[28px] border border-slate-200/70 bg-white/88 p-5 shadow-panel backdrop-blur dark:border-white/10 dark:bg-slate-900/86 sm:p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-slate-500 dark:text-slate-400">CNN 恐贪指数</p>
          <h3 className="mt-2 font-display text-xl font-semibold text-slate-950 dark:text-slate-50">Fear &amp; Greed</h3>
        </div>
        <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-500 dark:border-white/10 dark:bg-slate-950/70 dark:text-slate-400">
          {snapshot.as_of_date ? formatCompactDate(snapshot.as_of_date) : "--"}
        </div>
      </div>

      <div className="mt-4">
        <GaugeChart value={snapshot.value} />
      </div>

      <div className="mt-auto border-t border-slate-100 pt-4 dark:border-white/10">
        <div className="mb-3 flex items-center justify-between text-xs text-slate-400 dark:text-slate-500">
          <span>历史走势 (30天)</span>
          <span className="metric-number">
            最低 {formatNumber(trend.min_value, 0)} / 最高 {formatNumber(trend.max_value, 0)}
          </span>
        </div>
        <Sparkline
          data={trend.series.map((item) => item.value)}
          labels={trend.series.map((item) => formatCompactDate(item.trade_date))}
          color={color}
          height={56}
        />
      </div>
    </section>
  );
}
