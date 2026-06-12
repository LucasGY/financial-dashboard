import { AlertCircle } from "lucide-react";
import { useDeferredValue, useId, useState } from "react";
import { useLanguage } from "../../../app/language";
import { Sparkline } from "../../../components/charts/Sparkline";
import { AsyncState } from "../../../components/ui/AsyncState";
import { formatCompactDate, formatMonthDate, formatNumber } from "../../../lib/format";
import { useValuationTimeline } from "../hooks";
import type { ValuationTimelineResponse, ValuationWindow } from "../types";

type ValuationCardProps = {
  index: "SPX" | "NDX";
  title: string;
};

const WINDOWS: ValuationWindow[] = ["1y", "5y", "10y"];

const formatSignedPercent = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "--";
  }

  const percent = value * 100;
  const sign = percent > 0 ? "+" : "";
  return `${sign}${percent.toFixed(2)}%`;
};

const buildEstimateTooltip = (data: ValuationTimelineResponse, isZh: boolean) => {
  const estimatedDate = data.estimated_date ?? data.as_of_date;
  const displayEstimatedDate = estimatedDate ? formatCompactDate(estimatedDate, isZh ? "zh" : "en") : "--";
  const displayBaseDate = data.based_on_trade_date ? formatCompactDate(data.based_on_trade_date, isZh ? "zh" : "en") : "--";
  const displayWindow = data.window.toUpperCase();

  if (!data.is_estimated) {
    return isZh
      ? `数据日期：${displayEstimatedDate}。方式：FacSet 原始 PE (NTM)；分位数按当前 ${displayWindow} 窗口样本计算。`
      : `Data date: ${displayEstimatedDate}. Method: original FacSet PE (NTM); percentile is calculated from the current ${displayWindow} window.`;
  }

  if (isZh) {
    return `估算日期：${displayEstimatedDate}。方式：以 ${displayBaseDate} 的原始 PE ${formatNumber(data.raw_pe_ntm, 2)} 为基准，按 ${data.proxy_ticker ?? "--"} 从基准日至估算日的价格涨跌幅 ${formatSignedPercent(data.proxy_return)} 调整；分位数按当前 ${displayWindow} 窗口样本计算。`;
  }

  return `Estimated date: ${displayEstimatedDate}. Method: starts from the ${displayBaseDate} raw PE ${formatNumber(data.raw_pe_ntm, 2)} and adjusts by ${data.proxy_ticker ?? "--"} price return ${formatSignedPercent(data.proxy_return)} through the estimate date; percentile is calculated from the current ${displayWindow} window.`;
};

export function ValuationCard({ index, title }: ValuationCardProps) {
  const { isZh } = useLanguage();
  const [window, setWindow] = useState<ValuationWindow>("10y");
  const deferredWindow = useDeferredValue(window);
  const estimateTooltipId = useId();
  const { data, error, isLoading } = useValuationTimeline(index, deferredWindow);
  const isEmpty = !data || data.series.length === 0;
  const estimateTooltip = data ? buildEstimateTooltip(data, isZh) : "";

  return (
    <AsyncState isLoading={isLoading} error={error} isEmpty={isEmpty} emptyLabel={isZh ? `${title} 暂无估值数据` : `${title} valuation data is unavailable`}>
      {data ? (
        <section className="flex h-full flex-col rounded-[28px] border border-slate-200/70 bg-white/88 p-5 shadow-panel backdrop-blur dark:border-white/10 dark:bg-slate-900/86 sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-slate-500 dark:text-slate-400">{title}</p>
              <h3 className="mt-2 font-display text-xl font-semibold text-slate-950 dark:text-slate-50">{isZh ? "PE (NTM) 估值" : "PE (NTM) Valuation"}</h3>
              <p className="mt-2 flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400">
                <button
                  type="button"
                  aria-describedby={estimateTooltipId}
                  aria-label={isZh ? "估算说明" : "Estimate details"}
                  className="group relative inline-flex size-4 cursor-help items-center justify-center rounded-full text-slate-500 outline-none transition hover:text-slate-700 focus-visible:text-slate-700 focus-visible:ring-2 focus-visible:ring-blue-500/50 dark:text-slate-400 dark:hover:text-slate-200 dark:focus-visible:text-slate-200"
                >
                  <AlertCircle className="size-4" aria-hidden="true" />
                  <span
                    id={estimateTooltipId}
                    role="tooltip"
                    className="pointer-events-none absolute left-0 top-6 z-30 hidden w-64 rounded-md border border-slate-200 bg-white px-3 py-2 text-left text-xs leading-relaxed text-slate-700 shadow-lg group-focus:block group-hover:block dark:border-white/10 dark:bg-slate-950 dark:text-slate-200"
                  >
                    {estimateTooltip}
                  </span>
                </button>
                {isZh ? "最新日期" : "Latest date"} {data.as_of_date ? formatCompactDate(data.as_of_date) : "--"}
              </p>
            </div>
            <div className="flex rounded-full border border-slate-200 bg-slate-50 p-1 dark:border-white/10 dark:bg-slate-950/70">
              {WINDOWS.map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => setWindow(item)}
                  className={`rounded-full px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.12em] transition ${
                    window === item ? "bg-white text-blue-700 shadow-sm dark:bg-amber-400 dark:text-slate-950" : "text-slate-500 dark:text-slate-400"
                  }`}
                >
                  {item}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-6 flex items-end gap-3">
            <div className="metric-number text-4xl font-semibold text-slate-950 dark:text-slate-50">{formatNumber(data.current_value, 1)}</div>
            <div className="pb-1">
              <div className="text-xs text-slate-500 dark:text-slate-400">{isZh ? `当前处于 ${data.window.toUpperCase()}` : `Current ${data.window.toUpperCase()} window`}</div>
              <div
                className={`metric-number text-sm font-semibold ${
                  (data.percentile ?? 0) > 80 ? "text-rose-600" : (data.percentile ?? 0) < 20 ? "text-emerald-600" : "text-slate-700 dark:text-slate-200"
                }`}
              >
                {isZh ? `${formatNumber(data.percentile, 1)}% 分位` : `${formatNumber(data.percentile, 1)}% percentile`}
              </div>
            </div>
          </div>

          <div className="mt-6 flex-1">
            <Sparkline
              data={data.series.map((item) => item.value)}
              labels={data.series.map((item) => (data.window === "1y" ? formatCompactDate(item.trade_date, isZh ? "zh" : "en") : formatMonthDate(item.trade_date, isZh ? "zh" : "en")))}
              color={(data.percentile ?? 0) > 80 ? "#ef4444" : "#2563eb"}
              height={112}
              showLatestValueLine
            />
          </div>
        </section>
      ) : null}
    </AsyncState>
  );
}
