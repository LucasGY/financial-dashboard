import type { TimeSeriesPoint } from "../sentiment/types";

export type ValuationWindow = "1y" | "5y" | "10y";
export type AttributionTag = "week" | "month";

export type ValuationTimelineResponse = {
  index_code: "SPX" | "NDX";
  display_name: string;
  window: ValuationWindow;
  as_of_date: string | null;
  estimated_date: string | null;
  estimate_method: "facset" | "proxy_adjusted" | string;
  valuation_source: "facset" | "proxy_adjusted" | string;
  is_estimated: boolean;
  raw_pe_ntm: number | null;
  based_on_trade_date: string | null;
  proxy_ticker: string | null;
  proxy_return: number | null;
  current_value: number | null;
  percentile: number | null;
  series: TimeSeriesPoint[];
};

export type PriceAttributionPoint = {
  label: string;
  start_date: string;
  end_date: string;
  price_start: number | null;
  price_end: number | null;
  eps_start: number | null;
  eps_end: number | null;
  pe_start: number | null;
  pe_end: number | null;
  total_return: number | null;
  eps_contribution: number | null;
  valuation_contribution: number | null;
};

export type PriceAttributionResponse = {
  index_code: "SPX" | "NDX";
  display_name: string;
  ticker: string;
  tag: AttributionTag;
  as_of_date: string | null;
  series: PriceAttributionPoint[];
};
