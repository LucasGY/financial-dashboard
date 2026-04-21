import { BrainCircuit, Code2, Database, LineChart, Play, TerminalSquare } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { BarOverviewChart } from "../../../components/charts/BarOverviewChart";
import { SignalLineChart } from "../../../components/charts/SignalLineChart";
import { formatCompactDate, formatNumber, formatPercent } from "../../../lib/format";
import { useStrategyLab } from "../hooks";
import type { StrategyLabRunRequest, SupportedTicker } from "../types";

const TICKERS: SupportedTicker[] = ["SPY", "QQQ", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA"];
const DEFAULT_PROMPT =
  "当恐贪指数低于20且VIX高于25时，买入SPY，持有5、20、60个交易日";

const isoDate = (value: Date) => value.toISOString().slice(0, 10);

const inferTargetTicker = (prompt: string): SupportedTicker | null => {
  const normalized = prompt.toUpperCase();
  const explicitTickers: SupportedTicker[] = ["SPY", "QQQ", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA"];
  const matchedTicker = explicitTickers.find((ticker) => normalized.includes(ticker));
  if (matchedTicker) {
    return matchedTicker;
  }
  if (prompt.includes("纳指") || normalized.includes("NDX") || normalized.includes("NASDAQ-100") || normalized.includes("NASDAQ 100")) {
    return "QQQ";
  }
  if (prompt.includes("标普") || normalized.includes("SPX") || normalized.includes("S&P 500") || normalized.includes("SP500")) {
    return "SPY";
  }
  return null;
};

const inferForwardWindows = (prompt: string): number[] => {
  const normalized = prompt.replace(/\s+/g, "");
  const match = normalized.match(/持有([0-9、，,和与及]+)(?:个?交易?日|天|日)/);
  if (!match) {
    return [];
  }

  const windows = match[1]
    .split(/[、，,和与及]+/)
    .map((item) => Number.parseInt(item, 10))
    .filter((item) => Number.isFinite(item) && item > 0);

  return Array.from(new Set(windows)).sort((left, right) => left - right);
};

export function StrategyLabPanel() {
  const today = useMemo(() => new Date(), []);
  const initialStart = new Date(today);
  initialStart.setFullYear(initialStart.getFullYear() - 1);

  const [prompt, setPrompt] = useState(DEFAULT_PROMPT);
  const [targetTicker, setTargetTicker] = useState<SupportedTicker>("SPY");
  const [startDate, setStartDate] = useState(isoDate(initialStart));
  const [endDate, setEndDate] = useState(isoDate(today));
  const [windowsInput, setWindowsInput] = useState("5,20,60");
  const { submit, result, status, isSubmitting, error } = useStrategyLab();

  useEffect(() => {
    const inferredTicker = inferTargetTicker(prompt);
    if (inferredTicker && inferredTicker !== targetTicker) {
      setTargetTicker(inferredTicker);
    }
  }, [prompt, targetTicker]);

  useEffect(() => {
    const inferredWindows = inferForwardWindows(prompt);
    if (inferredWindows.length === 0) {
      return;
    }

    const nextValue = inferredWindows.join(",");
    if (nextValue !== windowsInput) {
      setWindowsInput(nextValue);
    }
  }, [prompt, windowsInput]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const forwardWindows = windowsInput
      .split(/[，,\s]+/)
      .map((item) => Number.parseInt(item, 10))
      .filter((item) => Number.isFinite(item) && item > 0);

    const payload: StrategyLabRunRequest = {
      prompt,
      target_ticker: targetTicker,
      start_date: startDate,
      end_date: endDate,
      forward_windows: forwardWindows
    };
    await submit(payload);
  };

  return (
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-[0.96fr_1.04fr]">
      <section className="rounded-[28px] border border-slate-200/70 bg-white/88 p-5 shadow-panel backdrop-blur sm:p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">
              <BrainCircuit className="size-3.5" />
              Strategy Lab
            </div>
            <h3 className="mt-4 font-display text-2xl font-semibold text-slate-950">自然语言生成回测</h3>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              输入策略描述，解析成受控规则，直接读取数据库指标与价格序列完成未来胜率和回报统计。
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-right">
            <div className="text-xs uppercase tracking-[0.16em] text-slate-400">状态</div>
            <div className="mt-2 text-sm font-semibold text-slate-700">{isSubmitting ? "Running" : status.toUpperCase()}</div>
          </div>
        </div>

        <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
          <label className="block space-y-2">
            <span className="text-sm font-semibold text-slate-700">策略描述</span>
            <textarea
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              rows={6}
              className="w-full rounded-[22px] border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm leading-6 text-slate-700 outline-none transition focus:border-blue-300 focus:bg-white"
            />
          </label>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label className="block space-y-2">
              <span className="text-sm font-semibold text-slate-700">回测标的</span>
              <select
                value={targetTicker}
                onChange={(event) => setTargetTicker(event.target.value as SupportedTicker)}
                className="w-full rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm text-slate-700 outline-none focus:border-blue-300 focus:bg-white"
              >
                {TICKERS.map((ticker) => (
                  <option key={ticker} value={ticker}>
                    {ticker}
                  </option>
                ))}
              </select>
              <p className="mt-2 text-xs leading-5 text-slate-400">当 prompt 中出现 QQQ/SPY/纳指/标普 等语义时，这里会自动同步。</p>
            </label>

            <label className="block space-y-2">
              <span className="text-sm font-semibold text-slate-700">未来窗口</span>
              <input
                value={windowsInput}
                onChange={(event) => setWindowsInput(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm text-slate-700 outline-none focus:border-blue-300 focus:bg-white"
                placeholder="5,20,60"
              />
              <p className="mt-2 text-xs leading-5 text-slate-400">当 prompt 中写了“持有 90 天”或“持有 5、20、60 个交易日”时，这里会自动同步。</p>
            </label>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label className="block space-y-2">
              <span className="text-sm font-semibold text-slate-700">开始日期</span>
              <input
                type="date"
                value={startDate}
                onChange={(event) => setStartDate(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm text-slate-700 outline-none focus:border-blue-300 focus:bg-white"
              />
            </label>
            <label className="block space-y-2">
              <span className="text-sm font-semibold text-slate-700">结束日期</span>
              <input
                type="date"
                value={endDate}
                onChange={(event) => setEndDate(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm text-slate-700 outline-none focus:border-blue-300 focus:bg-white"
              />
            </label>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex items-center gap-2 rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            <Play className="size-4" />
            {isSubmitting ? "正在回测..." : "运行策略"}
          </button>
        </form>
      </section>

      <section className="space-y-5">
        {error ? (
          <div className="rounded-[28px] border border-rose-200 bg-rose-50 px-6 py-5 text-sm leading-6 text-rose-700 shadow-panel">
            {error}
          </div>
        ) : null}

        {result ? (
          <>
            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
              <article className="rounded-[28px] border border-slate-200/70 bg-white/88 p-5 shadow-panel backdrop-blur">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-500">
                  <Database className="size-4" />
                  策略摘要
                </div>
                <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-slate-400">标的</div>
                    <div className="mt-1 font-semibold text-slate-800">{result.strategy_spec.target_ticker}</div>
                  </div>
                  <div>
                    <div className="text-slate-400">执行模式</div>
                    <div className="mt-1 font-semibold text-slate-800">{result.strategy_spec.execution_mode}</div>
                  </div>
                  <div>
                    <div className="text-slate-400">持有天数</div>
                    <div className="mt-1 font-semibold text-slate-800">{result.strategy_spec.holding_period_days}D</div>
                  </div>
                  <div>
                    <div className="text-slate-400">信号逻辑</div>
                    <div className="mt-1 font-semibold text-slate-800">{result.strategy_spec.logic_operator === "all" ? "AND" : "OR"}</div>
                  </div>
                </div>
                <div className="mt-5 space-y-2 text-sm text-slate-600">
                  {result.strategy_spec.entry_conditions.map((item) => (
                    <div key={`${item.indicator}-${item.description}`} className="rounded-2xl bg-slate-50 px-3 py-2">
                      {item.description}
                    </div>
                  ))}
                </div>
                {result.strategy_spec.parse_notes.length > 0 ? (
                  <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-6 text-amber-800">
                    {result.strategy_spec.parse_notes.join(" ")}
                  </div>
                ) : null}
              </article>

              <article className="rounded-[28px] border border-slate-200/70 bg-white/88 p-5 shadow-panel backdrop-blur">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-500">
                  <Code2 className="size-4" />
                  生成代码
                </div>
                <pre className="mt-4 overflow-x-auto rounded-[22px] bg-slate-950 p-4 text-xs leading-6 text-slate-100">
                  <code>{result.generated_code}</code>
                </pre>
              </article>
            </div>

            <article className="rounded-[28px] border border-slate-200/70 bg-white/88 p-5 shadow-panel backdrop-blur">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-500">
                <TerminalSquare className="size-4" />
                回测统计
              </div>
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full border-separate border-spacing-y-2 text-sm">
                  <thead>
                    <tr className="text-left text-slate-400">
                      <th className="px-3 py-2">窗口</th>
                      <th className="px-3 py-2">信号数</th>
                      <th className="px-3 py-2">胜率</th>
                      <th className="px-3 py-2">平均回报</th>
                      <th className="px-3 py-2">中位回报</th>
                      <th className="px-3 py-2">最大</th>
                      <th className="px-3 py-2">最小</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.summary_metrics.map((item) => (
                      <tr key={item.window_days} className="rounded-2xl bg-slate-50 text-slate-700">
                        <td className="rounded-l-2xl px-3 py-3 font-semibold">{item.window_days}D</td>
                        <td className="px-3 py-3 metric-number">{item.signal_count}</td>
                        <td className="px-3 py-3 metric-number">{formatPercent(item.win_rate, 1)}</td>
                        <td className="px-3 py-3 metric-number">{formatPercent(item.avg_return, 2)}</td>
                        <td className="px-3 py-3 metric-number">{formatPercent(item.median_return, 2)}</td>
                        <td className="px-3 py-3 metric-number">{formatPercent(item.max_return, 2)}</td>
                        <td className="rounded-r-2xl px-3 py-3 metric-number">{formatPercent(item.min_return, 2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </article>

            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
              <article className="rounded-[28px] border border-slate-200/70 bg-white/88 p-5 shadow-panel backdrop-blur">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-500">
                  <LineChart className="size-4" />
                  胜率分布
                </div>
                <div className="mt-4">
                  <BarOverviewChart bars={result.charts.win_rate_bars} formatValue={(value) => formatPercent(value, 1)} />
                </div>
              </article>
              <article className="rounded-[28px] border border-slate-200/70 bg-white/88 p-5 shadow-panel backdrop-blur">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-500">
                  <LineChart className="size-4" />
                  平均回报
                </div>
                <div className="mt-4">
                  <BarOverviewChart bars={result.charts.avg_return_bars} formatValue={(value) => formatPercent(value, 2)} />
                </div>
              </article>
            </div>

            <article className="rounded-[28px] border border-slate-200/70 bg-white/88 p-5 shadow-panel backdrop-blur">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-500">
                <LineChart className="size-4" />
                价格与信号
              </div>
              <div className="mt-4">
                <SignalLineChart priceSeries={result.charts.price_series} signalPoints={result.charts.signal_points} />
              </div>
            </article>

            <article className="rounded-[28px] border border-slate-200/70 bg-white/88 p-5 shadow-panel backdrop-blur">
              <div className="flex flex-wrap items-center gap-4 text-sm text-slate-500">
                <span>价格样本 {result.data_coverage.available_start_date ? formatCompactDate(result.data_coverage.available_start_date) : "--"} - {result.data_coverage.available_end_date ? formatCompactDate(result.data_coverage.available_end_date) : "--"}</span>
                <span>特征样本 {result.data_coverage.feature_start_date ? formatCompactDate(result.data_coverage.feature_start_date) : "--"} - {result.data_coverage.feature_end_date ? formatCompactDate(result.data_coverage.feature_end_date) : "--"}</span>
                <span>截断信号 {formatNumber(result.data_coverage.truncated_signal_count, 0)}</span>
              </div>
              {result.data_coverage.missing_features.length > 0 ? (
                <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                  缺失或不完整特征：{result.data_coverage.missing_features.join(", ")}
                </div>
              ) : null}
              {result.warnings.length > 0 ? (
                <div className="mt-4 space-y-2">
                  {result.warnings.map((item) => (
                    <div key={item} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                      {item}
                    </div>
                  ))}
                </div>
              ) : null}
            </article>
          </>
        ) : (
          <div className="flex min-h-[320px] items-center justify-center rounded-[28px] border border-dashed border-slate-300 bg-white/65 px-6 py-10 text-center text-sm leading-6 text-slate-500 shadow-panel">
            运行一次策略后，这里会展示解析结果、生成代码、回测表格和信号图。
          </div>
        )}
      </section>
    </div>
  );
}
