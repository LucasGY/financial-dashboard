import { getJson } from "../../lib/api/client";
import type { BreadthTrendResponse, FearGreedTrendResponse, SentimentOverviewResponse, VolatilityTrendResponse } from "./types";

export const getSentimentOverview = () => getJson<SentimentOverviewResponse>("/sentiment/overview");

export const getFearGreedTrend = () =>
  getJson<FearGreedTrendResponse>("/sentiment/fear-greed/trend", {
    range: "30d"
  });

export const getVolatilityTrend = () =>
  getJson<VolatilityTrendResponse>("/sentiment/volatility/trend", {
    range: "30d"
  });

export const getBreadthTrend = (index: "SPX" | "NDX") =>
  getJson<BreadthTrendResponse>("/sentiment/breadth/trend", {
    index,
    range: "30d"
  });
