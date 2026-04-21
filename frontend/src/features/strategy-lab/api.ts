import { getJson, postJson } from "../../lib/api/client";
import type { StrategyLabResult, StrategyLabRunRequest, StrategyRunResponse } from "./types";

export const createStrategyLabRun = (body: StrategyLabRunRequest) =>
  postJson<StrategyRunResponse, StrategyLabRunRequest>("/strategy-lab/runs", body);

export const getStrategyLabRunStatus = (runId: string) => getJson<StrategyRunResponse>(`/strategy-lab/runs/${runId}`);

export const getStrategyLabRunResult = (runId: string) => getJson<StrategyLabResult>(`/strategy-lab/runs/${runId}/result`);
