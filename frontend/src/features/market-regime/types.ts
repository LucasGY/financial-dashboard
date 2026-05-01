export type MarketRegimeCondition = {
  key: string;
  label: string;
  value: number | null;
  unit: string | null;
  bucket: number | null;
  percentile: number | null;
  bucket_label: string;
};

export type MarketRegimeMetric = {
  window_days: number;
  signal_count: number;
  win_rate: number | null;
  avg_return: number | null;
  median_return: number | null;
  max_return: number | null;
  min_return: number | null;
};

export type MarketRegimeStatsResponse = {
  ticker: "SPY" | "QQQ";
  index_code: "SPX" | "NDX";
  window: MarketRegimeWindow;
  as_of_date: string | null;
  entry_price: number | null;
  conditions: MarketRegimeCondition[];
  metrics: MarketRegimeMetric[];
  warnings: string[];
};

export type MarketRegimeOverviewResponse = {
  window: MarketRegimeWindow;
  items: MarketRegimeStatsResponse[];
};

export type MarketRegimeWindow = "1y" | "5y" | "10y";
