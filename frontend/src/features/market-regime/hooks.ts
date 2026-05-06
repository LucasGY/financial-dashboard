import { useAsyncData } from "../../lib/hooks";
import { getMarketRegimeOverview } from "./api";
import type { MarketRegimeStatsResponse, MarketRegimeWindow } from "./types";

type MarketRegimeResult = {
  data: MarketRegimeStatsResponse | null;
  error: string | null;
};

export function useMarketRegimeStats(window: MarketRegimeWindow) {
  return useAsyncData(async () => {
    const overview = await getMarketRegimeOverview(window);
    const byTicker = Object.fromEntries(overview.items.map((item) => [item.ticker, item]));
    const missing = (ticker: "SPY" | "QQQ"): MarketRegimeResult => ({
      data: null,
      error: `${ticker} 数据暂不可用`
    });

    return {
      spy: byTicker.SPY ? { data: byTicker.SPY, error: null } : missing("SPY"),
      qqq: byTicker.QQQ ? { data: byTicker.QQQ, error: null } : missing("QQQ")
    };
  }, [window]);
}
