import { useLanguage } from "../../../app/language";
import { Sparkline } from "../../../components/charts/Sparkline";
import { formatCompactDate, formatNumber } from "../../../lib/format";
import type { ValueSnapshot, VolatilityTrendResponse } from "../types";

type VolatilityCardProps = {
  vix: ValueSnapshot;
  volStructure: ValueSnapshot;
  trend: VolatilityTrendResponse;
};

function MetricBlock({
  title,
  value,
  data,
  color
}: {
  title: string;
  value: number | null;
  data: VolatilityTrendResponse["vix_series"];
  color: string;
}) {
  return (
    <div className="rounded-[24px] bg-slate-50/90 p-4 dark:bg-slate-950/58">
      <div className="flex items-end justify-between gap-3">
        <div className="text-sm font-medium text-slate-600 dark:text-slate-400">{title}</div>
        <div className="metric-number text-2xl font-semibold text-slate-950 dark:text-slate-50">{formatNumber(value, 2)}</div>
      </div>
      <div className="mt-3">
        <Sparkline
          data={data.map((item) => item.value)}
          labels={data.map((item) => formatCompactDate(item.trade_date))}
          color={color}
          height={52}
        />
      </div>
    </div>
  );
}

export function VolatilityCard({ vix, volStructure, trend }: VolatilityCardProps) {
  const { isZh } = useLanguage();
  return (
    <section className="flex h-full flex-col rounded-[28px] border border-slate-200/70 bg-white/88 p-5 shadow-panel backdrop-blur dark:border-white/10 dark:bg-slate-900/86 sm:p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-slate-500 dark:text-slate-400">{isZh ? "波动率指标" : "Volatility Metrics"}</p>
          <h3 className="mt-2 font-display text-xl font-semibold text-slate-950 dark:text-slate-50">Volatility</h3>
        </div>
        <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-500 dark:border-white/10 dark:bg-slate-950/70 dark:text-slate-400">
          {trend.as_of_date ? formatCompactDate(trend.as_of_date) : formatCompactDate(vix.as_of_date)}
        </div>
      </div>

      <div className="mt-5 flex-1 space-y-4">
        <MetricBlock title={isZh ? "VIX (恐慌指数)" : "VIX (Fear Index)"} value={vix.value ?? trend.vix_current} data={trend.vix_series} color="#f59e0b" />
        <MetricBlock
          title={isZh ? "VVIX / VIX / 3.5 (波动率结构)" : "VVIX / VIX / 3.5 (Volatility Structure)"}
          value={volStructure.value ?? trend.vol_structure_current}
          data={trend.vol_structure_series}
          color="#10b981"
        />
      </div>
    </section>
  );
}
