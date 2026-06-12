import { AlertTriangle, BadgeDollarSign, CircleDot } from "lucide-react";
import type { ReactNode } from "react";
import { useLanguage } from "../../../app/language";
import { AsyncState } from "../../../components/ui/AsyncState";
import { formatCompactDate, formatNumber, formatPercent } from "../../../lib/format";
import { useDrawdownScenarios } from "../hooks";
import type { DrawdownScenarioPoint, DrawdownScenarioTable } from "../types";

const formatDrawdown = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "--";
  }
  return `${value.toFixed(value % 1 === 0 ? 0 : 1)}%`;
};

const rowClassName = (row: DrawdownScenarioPoint) => {
  if (row.is_current_drawdown_row) {
    return "bg-blue-500/12 text-blue-950 ring-1 ring-inset ring-blue-400/40 dark:bg-blue-400/14 dark:text-blue-100 dark:ring-blue-300/30";
  }
  if (row.is_cheap) {
    return "bg-emerald-500/12 text-emerald-950 dark:bg-emerald-400/12 dark:text-emerald-100";
  }
  if (row.is_key_drawdown) {
    return "bg-amber-400/14 text-amber-950 dark:bg-amber-300/12 dark:text-amber-100";
  }
  return "text-slate-700 dark:text-slate-200";
};

function ScenarioTable({ table }: { table: DrawdownScenarioTable }) {
  const { isZh } = useLanguage();

  return (
    <article className="rounded-[28px] border border-slate-200/70 bg-white/88 p-5 shadow-panel backdrop-blur dark:border-white/10 dark:bg-slate-900/86">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-slate-500 dark:text-slate-400">{table.ticker}</p>
          <h3 className="mt-1 font-display text-xl font-semibold text-slate-950 dark:text-slate-50">
            {isZh ? `${table.display_name} 回撤情景` : `${table.display_name} Drawdown Scenarios`}
          </h3>
        </div>
        <div className="text-right text-xs text-slate-500 dark:text-slate-400">
          <div>{table.as_of_date ? formatCompactDate(table.as_of_date, isZh ? "zh" : "en") : "--"}</div>
          <div className="mt-1 font-semibold text-slate-700 dark:text-slate-200">{formatDrawdown(table.current_drawdown_pct)}</div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
        <Metric label={isZh ? "现价" : "Current"} value={formatNumber(table.current_price, 2)} />
        <Metric label={isZh ? "高点" : "High"} value={formatNumber(table.high_price, 2)} />
        <Metric label={isZh ? "当前 PE" : "Current PE"} value={formatNumber(table.current_pe, 2)} />
      </div>

      <div className="mt-4 flex flex-wrap gap-2 text-[11px] font-semibold">
        <Legend icon={<CircleDot className="size-3" />} label={isZh ? "当前实际回撤" : "Current drawdown"} className="bg-blue-500/12 text-blue-700 dark:text-blue-200" />
        <Legend icon={<AlertTriangle className="size-3" />} label="-5% / -10% / -15%" className="bg-amber-400/14 text-amber-700 dark:text-amber-200" />
        <Legend icon={<BadgeDollarSign className="size-3" />} label={isZh ? "5Y/10Y < 20%" : "5Y/10Y < 20%"} className="bg-emerald-500/12 text-emerald-700 dark:text-emerald-200" />
      </div>

      <div className="mt-4 overflow-x-auto">
        <table className="min-w-[620px] w-full border-separate border-spacing-y-1 text-left text-xs">
          <thead className="text-[11px] uppercase tracking-[0.12em] text-slate-400 dark:text-slate-500">
            <tr>
              <th className="px-3 py-2">{isZh ? "回撤" : "Drawdown"}</th>
              <th className="px-3 py-2">{isZh ? "点位" : "Level"}</th>
              <th className="px-3 py-2">{isZh ? "隐含 PE" : "Implied PE"}</th>
              <th className="px-3 py-2">1Y</th>
              <th className="px-3 py-2">5Y</th>
              <th className="px-3 py-2">10Y</th>
            </tr>
          </thead>
          <tbody>
            {table.scenarios.map((row) => (
              <tr key={`${table.ticker}-${row.drawdown_pct}`} className={`rounded-lg ${rowClassName(row)}`}>
                <td className="rounded-l-lg px-3 py-2 font-semibold">{formatDrawdown(row.drawdown_pct)}</td>
                <td className="px-3 py-2 metric-number">{formatNumber(row.price_level, 2)}</td>
                <td className="px-3 py-2 metric-number">{formatNumber(row.implied_pe, 2)}</td>
                <td className="px-3 py-2 metric-number">{formatPercent(row.percentile_1y, 1)}</td>
                <td className="px-3 py-2 metric-number">{formatPercent(row.percentile_5y, 1)}</td>
                <td className="rounded-r-lg px-3 py-2 metric-number">{formatPercent(row.percentile_10y, 1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200/70 bg-slate-50 px-3 py-2 dark:border-white/10 dark:bg-slate-950/50">
      <div className="text-slate-500 dark:text-slate-400">{label}</div>
      <div className="metric-number mt-1 text-sm font-semibold text-slate-950 dark:text-slate-50">{value}</div>
    </div>
  );
}

function Legend({ icon, label, className }: { icon: ReactNode; label: string; className: string }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 ${className}`}>
      {icon}
      {label}
    </span>
  );
}

export function DrawdownScenarioCard() {
  const { isZh } = useLanguage();
  const { data, error, isLoading } = useDrawdownScenarios();
  const tables = data ? [data.spy, data.qqq].filter((item): item is DrawdownScenarioTable => item !== null) : [];
  const isEmpty = !data || tables.length === 0;

  return (
    <AsyncState isLoading={isLoading} error={error} isEmpty={isEmpty} emptyLabel={isZh ? "暂无回撤情景数据" : "Drawdown scenario data is unavailable"}>
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        {tables.map((table) => (
          <ScenarioTable key={table.ticker} table={table} />
        ))}
      </div>
    </AsyncState>
  );
}
