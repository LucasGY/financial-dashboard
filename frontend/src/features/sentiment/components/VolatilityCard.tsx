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
    <div className="rounded-[24px] bg-slate-50/90 p-4">
      <div className="flex items-end justify-between gap-3">
        <div className="text-sm font-medium text-slate-600">{title}</div>
        <div className="metric-number text-2xl font-semibold text-slate-950">{formatNumber(value, 2)}</div>
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
  return (
    <section className="rounded-[28px] border border-slate-200/70 bg-white/88 p-5 shadow-panel backdrop-blur sm:p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-slate-500">波动率指标</p>
          <h3 className="mt-2 font-display text-xl font-semibold text-slate-950">Volatility</h3>
        </div>
        <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-500">
          {trend.as_of_date ? formatCompactDate(trend.as_of_date) : formatCompactDate(vix.as_of_date)}
        </div>
      </div>

      <div className="mt-5 space-y-4">
        <MetricBlock title="VIX (恐慌指数)" value={vix.value ?? trend.vix_current} data={trend.vix_series} color="#f59e0b" />
        <MetricBlock
          title="VVIX / VIX / 3.5 (波动率结构)"
          value={volStructure.value ?? trend.vol_structure_current}
          data={trend.vol_structure_series}
          color="#10b981"
        />
      </div>
    </section>
  );
}
