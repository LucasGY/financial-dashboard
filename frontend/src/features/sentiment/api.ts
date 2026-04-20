import { getJson } from "../../lib/api/client";
import type { FearGreedTrendResponse, SentimentOverviewResponse, VolatilityTrendResponse } from "./types";

export const getSentimentOverview = () => getJson<SentimentOverviewResponse>("/sentiment/overview");

export const getFearGreedTrend = () =>
  getJson<FearGreedTrendResponse>("/sentiment/fear-greed/trend", {
    range: "30d"
  });

export const getVolatilityTrend = () =>
  getJson<VolatilityTrendResponse>("/sentiment/volatility/trend", {
    range: "30d"
  });
