import { getJson } from "../../lib/api/client";
import type { ValuationTimelineResponse, ValuationWindow } from "./types";

export const getValuationTimeline = (index: "SPX" | "NDX", window: ValuationWindow) =>
  getJson<ValuationTimelineResponse>("/valuation/timeline", {
    index,
    window
  });
