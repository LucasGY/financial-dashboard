import { getJson } from "../../lib/api/client";
import type { MarketRegimeOverviewResponse, MarketRegimeStatsResponse, MarketRegimeWindow } from "./types";

const wait = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

export const getMarketRegimeOverview = async (window: MarketRegimeWindow) => {
  const delays = [0, 800, 1600];
  let lastError: Error | null = null;

  for (const delay of delays) {
    if (delay > 0) {
      await wait(delay);
    }

    try {
      return await getJson<MarketRegimeOverviewResponse>("/market-regime/overview", {
        window
      });
    } catch (error) {
      lastError = error instanceof Error ? error : new Error("market regime data unavailable");
    }
  }

  throw lastError || new Error("market regime data unavailable");
};

export const getMarketRegimeStats = (ticker: "SPY" | "QQQ", window: MarketRegimeWindow = "1y") =>
  getJson<MarketRegimeStatsResponse>("/market-regime/stats", {
    ticker,
    window
  });
