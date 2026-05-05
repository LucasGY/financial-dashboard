import { TerminalSquare } from "lucide-react";
import { useDeferredValue, useState } from "react";
import { AsyncState } from "../../../components/ui/AsyncState";
import { formatCompactDate, formatNumber, formatPercent } from "../../../lib/format";
import { useMarketRegimeStats } from "../hooks";
import type { MarketRegimeMetric, MarketRegimeStatsResponse, MarketRegimeWindow } from "../types";

const WINDOWS: MarketRegimeWindow[] = ["1y", "5y", "10y"];

const valueTone = (value: number | null, kind: "winRate" | "return") => {
  if (value === null) {
    return "text-slate-400";
  }

  if (kind === "winRate") {
    if (value >= 65) {
      return "text-emerald-600";
    }
    if (value <= 45) {
      return "text-rose-600";
    }
    return "text-slate-800 dark:text-slate-200";
  }

  if (value >= 2) {
    return "text-emerald-600";
  }
  if (value < 0) {
    return "text-rose-600";
  }
  return "text-slate-800 dark:text-slate-200";
};

const conditionValue = (value: number | null, unit: string | null) => {
  if (value === null) {
    return "--";
  }
  return unit === "%" ? formatPercent(value, 0) : formatNumber(value, value >= 100 ? 0 : 1);
};

function MetricCell({ metric, field }: { metric: MarketRegimeMetric; field: "win_rate" | "avg_return" }) {
  const value = metric[field];
  const kind = field === "win_rate" ? "winRate" : "return";
  return (
    <span className={`metric-number font-semibold ${valueTone(value, kind)}`}>
      {field === "win_rate" ? formatPercent(value, 1) : formatPercent(value, 2)}
    </span>
  );
}

function RegimeStatsCard({ data }: { data: MarketRegimeStatsResponse }) {
  return (
    <section className="rounded-[28px] border border-slate-200/70 bg-white/88 p-5 shadow-panel backdrop-blur dark:border-white/10 dark:bg-slate-900/86 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-slate-500 dark:text-slate-400">{data.ticker} / {data.index_code}</p>
          <h3 className="mt-2 font-display text-xl font-semibold text-slate-950 dark:text-slate-50">当前状态回测统计</h3>
          <p className="mt-2 flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400">
            <TerminalSquare className="size-4" />
            {data.window.toUpperCase()} · 最新收盘 {data.as_of_date ? formatCompactDate(data.as_of_date) : "--"} · {formatNumber(data.entry_price, 2)}
          </p>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        {data.conditions.map((condition) => (
          <div key={condition.key} className="rounded-2xl bg-slate-50 px-3 py-3 dark:bg-slate-950/58">
            <div className="text-xs font-medium text-slate-400 dark:text-slate-500">{condition.label}</div>
            <div className="metric-number mt-2 text-lg font-semibold text-slate-900 dark:text-slate-100">
              {conditionValue(condition.value, condition.unit)}
            </div>
            <div className="mt-1 text-xs font-semibold text-blue-600 dark:text-amber-300">{condition.bucket_label}</div>
          </div>
        ))}
      </div>

      <div className="mt-5 overflow-x-auto">
        <table className="w-full min-w-[560px] border-separate border-spacing-y-2 text-left">
          <thead>
            <tr className="text-sm font-semibold text-slate-400 dark:text-slate-500">
              <th className="px-4 py-2">窗口</th>
              <th className="px-4 py-2">信号数</th>
              <th className="px-4 py-2">胜率</th>
              <th className="px-4 py-2">平均回报</th>
              <th className="px-4 py-2">中位回报</th>
              <th className="px-4 py-2">最大</th>
              <th className="px-4 py-2">最小</th>
            </tr>
          </thead>
          <tbody>
            {data.metrics.map((metric) => (
              <tr key={metric.window_days} className="bg-slate-50/80 text-slate-800 dark:bg-slate-950/58 dark:text-slate-200">
                <td className="rounded-l-2xl px-4 py-3 font-semibold">{metric.window_days}D</td>
                <td className="metric-number px-4 py-3 font-semibold">{metric.signal_count}</td>
                <td className="px-4 py-3"><MetricCell metric={metric} field="win_rate" /></td>
                <td className="px-4 py-3"><MetricCell metric={metric} field="avg_return" /></td>
                <td className={`metric-number px-4 py-3 font-semibold ${valueTone(metric.median_return, "return")}`}>
                  {formatPercent(metric.median_return, 2)}
                </td>
                <td className={`metric-number px-4 py-3 font-semibold ${valueTone(metric.max_return, "return")}`}>
                  {formatPercent(metric.max_return, 2)}
                </td>
                <td className={`metric-number rounded-r-2xl px-4 py-3 font-semibold ${valueTone(metric.min_return, "return")}`}>
                  {formatPercent(metric.min_return, 2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data.warnings.length > 0 ? (
        <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-400/30 dark:bg-amber-400/10 dark:text-amber-200">
          {data.warnings.join(" ")}
        </div>
      ) : null}
    </section>
  );
}

function RegimeStatsErrorCard({ ticker, message }: { ticker: "SPY" | "QQQ"; message: string }) {
  return (
    <section className="rounded-[28px] border border-rose-200 bg-rose-50/80 p-5 shadow-panel dark:border-rose-400/30 dark:bg-rose-950/30 sm:p-6">
      <p className="text-sm font-semibold text-rose-500">{ticker}</p>
      <h3 className="mt-2 font-display text-xl font-semibold text-rose-700">数据加载失败</h3>
      <p className="mt-3 text-sm text-rose-600">{message}</p>
    </section>
  );
}

export function RegimeStatsPanel() {
  const [window, setWindow] = useState<MarketRegimeWindow>("1y");
  const deferredWindow = useDeferredValue(window);
  const { data, error, isLoading } = useMarketRegimeStats(deferredWindow);
  const isEmpty = !data || (!data.spy.data && !data.qqq.data);

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <div className="flex rounded-full border border-slate-200 bg-white/80 p-1 shadow-sm dark:border-white/10 dark:bg-slate-900/80">
          {WINDOWS.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => setWindow(item)}
              className={`rounded-full px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.12em] transition ${
                window === item ? "bg-blue-600 text-white shadow-sm dark:bg-amber-400 dark:text-slate-950" : "text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
              }`}
            >
              {item}
            </button>
          ))}
        </div>
      </div>

      <AsyncState isLoading={isLoading} error={error} isEmpty={isEmpty} emptyLabel="当前状态回测数据暂不可用">
        {data ? (
          <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
            {data.spy.data ? <RegimeStatsCard data={data.spy.data} /> : <RegimeStatsErrorCard ticker="SPY" message={data.spy.error || "数据源暂不可用"} />}
            {data.qqq.data ? <RegimeStatsCard data={data.qqq.data} /> : <RegimeStatsErrorCard ticker="QQQ" message={data.qqq.error || "数据源暂不可用"} />}
          </div>
        ) : null}
      </AsyncState>
    </div>
  );
}
