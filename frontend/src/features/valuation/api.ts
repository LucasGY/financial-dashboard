import { getJson } from "../../lib/api/client";
import type { AttributionTag, PriceAttributionResponse, ValuationTimelineResponse, ValuationWindow } from "./types";

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
