import { AlertCircle } from "lucide-react";
import { useDeferredValue, useState } from "react";
import { useLanguage } from "../../../app/language";
import { Sparkline } from "../../../components/charts/Sparkline";
import { AsyncState } from "../../../components/ui/AsyncState";
import { formatCompactDate, formatMonthDate, formatNumber } from "../../../lib/format";
import { useValuationTimeline } from "../hooks";
import type { ValuationWindow } from "../types";

type ValuationCardProps = {
  index: "SPX" | "NDX";
  title: string;
};

const WINDOWS: ValuationWindow[] = ["1y", "5y", "10y"];

export function ValuationCard({ index, title }: ValuationCardProps) {
  const { isZh } = useLanguage();
  const [window, setWindow] = useState<ValuationWindow>("10y");
  const deferredWindow = useDeferredValue(window);
  const { data, error, isLoading } = useValuationTimeline(index, deferredWindow);
  const isEmpty = !data || data.series.length === 0;

  return (
    <AsyncState isLoading={isLoading} error={error} isEmpty={isEmpty} emptyLabel={isZh ? `${title} 暂无估值数据` : `${title} valuation data is unavailable`}>
      {data ? (
        <section className="flex h-full flex-col rounded-[28px] border border-slate-200/70 bg-white/88 p-5 shadow-panel backdrop-blur dark:border-white/10 dark:bg-slate-900/86 sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-slate-500 dark:text-slate-400">{title}</p>
              <h3 className="mt-2 font-display text-xl font-semibold text-slate-950 dark:text-slate-50">{isZh ? "PE (NTM) 估值" : "PE (NTM) Valuation"}</h3>
              <p className="mt-2 flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400">
                <AlertCircle className="size-4" />
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
            />
          </div>
        </section>
      ) : null}
    </AsyncState>
  );
}
