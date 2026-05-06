import { useMemo, useState } from "react";
import { useLanguage } from "../../../app/language";
import { formatCompactDate, formatPercent } from "../../../lib/format";
import type { PriceAttributionPoint } from "../types";

type AttributionStackedBarChartProps = {
  data: PriceAttributionPoint[];
};

const EPS_COLOR = "#c85a96";
const VALUATION_COLOR = "#12bfa5";
const POSITIVE_GUIDE = "#2f9df4";
const NEGATIVE_GUIDE = "#ff6b36";

type Segment = {
  key: "eps" | "valuation";
  value: number;
  y: number;
  height: number;
  color: string;
};

const toPercent = (value: number, scale: number) => (Math.abs(value) / scale) * 46;

export function AttributionStackedBarChart({ data }: AttributionStackedBarChartProps) {
  const { isZh } = useLanguage();
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const visible = data.slice(-18);
  const scale = useMemo(() => {
    const extents = visible.flatMap((item) => {
      const eps = item.eps_contribution ?? 0;
      const valuation = item.valuation_contribution ?? 0;
      const positive = Math.max(eps, 0) + Math.max(valuation, 0);
      const negative = Math.abs(Math.min(eps, 0) + Math.min(valuation, 0));
      return [positive, negative, Math.abs(item.total_return ?? 0)];
    });
    return Math.max(...extents, 1);
  }, [visible]);

  if (visible.length === 0) {
    return <div className="flex h-[260px] items-center justify-center text-sm text-slate-500 dark:text-slate-400">{isZh ? "暂无归因数据" : "No attribution data"}</div>;
  }

  const active = hoverIndex === null ? visible[visible.length - 1] : visible[hoverIndex];

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4 text-slate-900 shadow-[inset_0_1px_0_rgba(255,255,255,0.55)] dark:border-slate-900 dark:bg-[#090a0c] dark:text-slate-100 dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
          <span className="inline-flex items-center gap-1.5">
            <span className="h-3 w-1.5 rounded-full" style={{ backgroundColor: EPS_COLOR }} />
            {isZh ? "EPS 贡献" : "EPS Contribution"}
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-3 w-1.5 rounded-full" style={{ backgroundColor: VALUATION_COLOR }} />
            {isZh ? "估值 / 情绪" : "Valuation / Sentiment"}
          </span>
        </div>
        <div className="metric-number rounded-md bg-white/80 px-2 py-1 text-xs text-slate-600 ring-1 ring-slate-200 dark:bg-white/[0.06] dark:text-slate-300 dark:ring-white/10">
          {formatCompactDate(active.start_date)} - {formatCompactDate(active.end_date)}
        </div>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,1fr)_210px]">
        <div className="min-w-0">
          <div className="relative h-[260px]">
            <div className="absolute left-0 right-0 top-1/2 h-px bg-slate-300/80 dark:bg-slate-700/80" />
            <div className="absolute bottom-0 left-0 top-0 flex flex-col justify-between text-[10px] text-slate-400 dark:text-slate-600">
              <span>{formatPercent(scale, 0)}</span>
              <span>0%</span>
              <span>-{formatPercent(scale, 0)}</span>
            </div>
            <div className="absolute inset-y-0 left-9 right-0 flex items-stretch gap-1.5">
              {visible.map((item, index) => {
                const eps = item.eps_contribution ?? 0;
                const valuation = item.valuation_contribution ?? 0;
                let positiveCursor = 50;
                let negativeCursor = 50;
                const rawSegments: Segment[] = [
                  { key: "eps", value: eps, y: 50, height: 0, color: EPS_COLOR },
                  { key: "valuation", value: valuation, y: 50, height: 0, color: VALUATION_COLOR }
                ];
                const segments = rawSegments.map((segment) => {
                  const height = Math.max(toPercent(segment.value, scale), segment.value === 0 ? 0 : 1.4);
                  if (segment.value >= 0) {
                    positiveCursor -= height;
                    return { ...segment, y: positiveCursor, height };
                  }

                  const y = negativeCursor;
                  negativeCursor += height;
                  return { ...segment, y, height };
                });
                const total = item.total_return ?? 0;
                const totalY = 50 - (total / scale) * 46;
                const showLabel = visible.length <= 14 || index % 2 === 0;

                return (
                  <button
                    key={`${item.start_date}-${item.end_date}`}
                    type="button"
                    className="group relative flex min-w-0 flex-1 flex-col justify-end"
                    onMouseEnter={() => setHoverIndex(index)}
                    onFocus={() => setHoverIndex(index)}
                    onMouseLeave={() => setHoverIndex(null)}
                    onBlur={() => setHoverIndex(null)}
                    aria-label={`${item.label} total return ${formatPercent(item.total_return)}`}
                  >
                    <div className="absolute inset-x-0 top-0 h-full rounded-sm bg-slate-900/[0.04] opacity-0 transition group-hover:opacity-100 group-focus:opacity-100 dark:bg-white/[0.02]" />
                    <div
                      className="absolute left-1/2 z-10 h-1.5 w-1.5 -translate-x-1/2 rounded-full border border-slate-950"
                      style={{ top: `calc(${totalY}% - 3px)`, backgroundColor: total >= 0 ? POSITIVE_GUIDE : NEGATIVE_GUIDE }}
                    />
                    {showLabel ? (
                      <div
                        className="metric-number absolute left-1/2 z-20 -translate-x-1/2 whitespace-nowrap rounded bg-white px-1.5 py-0.5 text-[10px] text-slate-900 opacity-0 shadow-sm ring-1 ring-slate-200 transition group-hover:opacity-100 group-focus:opacity-100 dark:bg-slate-950 dark:text-slate-100 dark:ring-white/10"
                        style={{ top: `calc(${Math.max(3, Math.min(92, totalY))}% - 24px)` }}
                      >
                        {formatPercent(total)}
                      </div>
                    ) : null}
                    {segments.map((segment) => (
                      <div
                        key={segment.key}
                        className="absolute left-[18%] right-[18%] rounded-[2px]"
                        style={{
                          top: `${segment.y}%`,
                          height: `${segment.height}%`,
                          backgroundColor: segment.color
                        }}
                      />
                    ))}
                  </button>
                );
              })}
            </div>
          </div>
          <div className="mt-2 grid grid-cols-[2.25rem_minmax(0,1fr)]">
            <div />
            <div className="grid text-[10px] text-slate-400 dark:text-slate-500" style={{ gridTemplateColumns: `repeat(${visible.length}, minmax(0, 1fr))` }}>
              {visible.map((item, index) => (
                <div key={`${item.start_date}-${item.end_date}-axis`} className="min-w-0 text-center">
                  {visible.length <= 10 || index % 3 === 0 ? item.label : ""}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white/70 p-3 dark:border-white/10 dark:bg-white/[0.03]">
          <div className="inline-flex rounded-md bg-white px-2 py-1 text-xs font-semibold text-slate-900 ring-1 ring-slate-200 dark:bg-white/[0.06] dark:text-slate-100 dark:ring-white/10">{active.label}</div>
          <div className="mt-4 space-y-3 text-sm">
            <MetricRow label={isZh ? "总回报" : "Total Return"} value={active.total_return} color={(active.total_return ?? 0) >= 0 ? POSITIVE_GUIDE : NEGATIVE_GUIDE} />
            <MetricRow label={isZh ? "EPS 贡献" : "EPS Contribution"} value={active.eps_contribution} color={EPS_COLOR} />
            <MetricRow label={isZh ? "估值 / 情绪" : "Valuation / Sentiment"} value={active.valuation_contribution} color={VALUATION_COLOR} />
          </div>
          <div className="mt-4 border-t border-slate-200 pt-3 text-xs text-slate-500 dark:border-white/10 dark:text-slate-400">
            <div className="flex justify-between">
              <span>PE</span>
              <span className="metric-number">
                {active.pe_start?.toFixed(1) ?? "--"} → {active.pe_end?.toFixed(1) ?? "--"}
              </span>
            </div>
            <div className="mt-2 flex justify-between">
              <span>{isZh ? "ETF 价格" : "ETF Price"}</span>
              <span className="metric-number">
                {active.price_start?.toFixed(1) ?? "--"} → {active.price_end?.toFixed(1) ?? "--"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricRow({ label, value, color }: { label: string; value: number | null; color: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="inline-flex items-center gap-2 text-slate-600 dark:text-slate-300">
        <span className="h-3 w-1.5 rounded-full" style={{ backgroundColor: color }} />
        {label}
      </span>
      <span className="metric-number font-semibold text-slate-900 dark:text-slate-50">{formatPercent(value)}</span>
    </div>
  );
}
