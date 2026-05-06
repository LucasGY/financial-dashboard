import type { TimeSeriesPoint } from "../sentiment/types";

export type ValuationWindow = "1y" | "5y" | "10y";

export type ValuationTimelineResponse = {
  index_code: "SPX" | "NDX";
  display_name: string;
  window: ValuationWindow;
  as_of_date: string | null;
  current_value: number | null;
  percentile: number | null;
  series: TimeSeriesPoint[];
};
