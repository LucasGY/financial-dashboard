import { getJson } from "../../lib/api/client";
import type { AttributionTag, DrawdownScenariosResponse, PriceAttributionResponse, ValuationTimelineResponse, ValuationWindow } from "./types";

export const getValuationTimeline = (index: "SPX" | "NDX", window: ValuationWindow) =>
  getJson<ValuationTimelineResponse>("/valuation/timeline", {
    index,
    window
  });

export const getPriceAttribution = (index: "SPX" | "NDX", tag: AttributionTag) =>
  getJson<PriceAttributionResponse>("/valuation/price-attribution", {
    index,
    tag
  });

export const getDrawdownScenarios = () => getJson<DrawdownScenariosResponse>("/valuation/drawdown-scenarios");
