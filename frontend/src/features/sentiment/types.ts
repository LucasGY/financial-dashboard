export type TimeSeriesPoint = {
  trade_date: string;
  value: number | null;
};

export type FearGreedSnapshot = {
  as_of_date: string;
  value: number | null;
  label: string | null;
  color: string | null;
  day_change: number | null;
};

export type ValueSnapshot = {
  as_of_date: string;
  value: number | null;
};

export type BreadthSnapshot = {
  index_code: "SPX" | "NDX";
  display_name: string;
  as_of_date: string;
  above_20d_pct: number | null;
  above_50d_pct: number | null;
  above_200d_pct: number | null;
};

export type SentimentOverviewResponse = {
  fear_greed: FearGreedSnapshot;
  vix: ValueSnapshot;
  vol_structure: ValueSnapshot;
  breadth: {
    spx: BreadthSnapshot | null;
    ndx: BreadthSnapshot | null;
  };
};

export type FearGreedTrendResponse = {
  range: string;
  as_of_date: string | null;
  start_value: number | null;
  end_value: number | null;
  min_value: number | null;
  max_value: number | null;
  series: TimeSeriesPoint[];
};

export type VolatilityTrendResponse = {
  range: string;
  as_of_date: string | null;
  vix_current: number | null;
  vol_structure_current: number | null;
  vix_series: TimeSeriesPoint[];
  vol_structure_series: TimeSeriesPoint[];
};
