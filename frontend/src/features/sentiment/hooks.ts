import { useAsyncData } from "../../lib/hooks";
import { getBreadthTrend, getFearGreedTrend, getSentimentOverview, getVolatilityTrend } from "./api";

export function useSentimentData() {
  return useAsyncData(async () => {
    const [overview, fearGreedTrend, volatilityTrend, spxBreadthTrend, ndxBreadthTrend] = await Promise.all([
      getSentimentOverview(),
      getFearGreedTrend(),
      getVolatilityTrend(),
      getBreadthTrend("SPX"),
      getBreadthTrend("NDX")
    ]);

    return {
      overview,
      fearGreedTrend,
      volatilityTrend,
      breadthTrend: {
        spx: spxBreadthTrend,
        ndx: ndxBreadthTrend
      }
    };
  }, []);
}
