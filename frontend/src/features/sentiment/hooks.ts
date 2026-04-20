import { useAsyncData } from "../../lib/hooks";
import { getFearGreedTrend, getSentimentOverview, getVolatilityTrend } from "./api";

export function useSentimentData() {
  return useAsyncData(async () => {
    const [overview, fearGreedTrend, volatilityTrend] = await Promise.all([
      getSentimentOverview(),
      getFearGreedTrend(),
      getVolatilityTrend()
    ]);

    return {
      overview,
      fearGreedTrend,
      volatilityTrend
    };
  }, []);
}
