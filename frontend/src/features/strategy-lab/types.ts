import type { TimeSeriesPoint } from "../sentiment/types";

export type SupportedTicker = "SPY" | "QQQ" | "AAPL" | "MSFT" | "AMZN" | "GOOGL" | "META" | "NVDA" | "TSLA";

export type StrategyLabRunRequest = {
  prompt: string;
  target_ticker: SupportedTicker;
  start_date: string;
  end_date: string;
  forward_windows: number[];
};

export type StrategyRunResponse = {
  run_id: string;
  status: "queued" | "running" | "succeeded" | "failed";
  message: string | null;
};

export type StrategyCondition = {
  indicator: string;
  operator: string;
  threshold: number | null;
  upper_threshold: number | null;
  consecutive_days: number;
  index_code: string | null;
  breadth_period: number | null;
  percentile_window: string | null;
  description: string;
};

export type StrategySpec = {
  prompt: string;
  target_ticker: SupportedTicker;
  logic_operator: "all" | "any";
  holding_period_days: number;
  forward_windows: number[];
  entry_conditions: StrategyCondition[];
  execution_mode: "rules" | "sandbox";
  parse_notes: string[];
  unsupported_fragments: string[];
};

export type SummaryMetric = {
  window_days: number;
  signal_count: number;
  win_rate: number | null;
  avg_return: number | null;
  median_return: number | null;
  max_return: number | null;
  min_return: number | null;
};

export type SignalEvent = {
  signal_date: string;
  entry_date: string | null;
  forward_returns: Record<string, number | null>;
  met_conditions: string[];
};

export type ChartBarPoint = {
  label: string;
  value: number | null;
};

export type SignalMarkerPoint = {
  trade_date: string;
  price: number;
  label: string;
};

export type StrategyCharts = {
  win_rate_bars: ChartBarPoint[];
  avg_return_bars: ChartBarPoint[];
  price_series: TimeSeriesPoint[];
  signal_points: SignalMarkerPoint[];
};

export type DataCoverage = {
  available_start_date: string | null;
  available_end_date: string | null;
  feature_start_date: string | null;
  feature_end_date: string | null;
  missing_features: string[];
  truncated_signal_count: number;
};

export type StrategyLabResult = {
  run_id: string;
  strategy_spec: StrategySpec;
  generated_code: string;
  summary_metrics: SummaryMetric[];
  signal_events: SignalEvent[];
  charts: StrategyCharts;
  data_coverage: DataCoverage;
  warnings: string[];
};
