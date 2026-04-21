import { useState } from "react";
import { createStrategyLabRun, getStrategyLabRunResult, getStrategyLabRunStatus } from "./api";
import type { StrategyLabResult, StrategyLabRunRequest } from "./types";

type StrategyLabState = {
  result: StrategyLabResult | null;
  runId: string | null;
  status: "idle" | "queued" | "running" | "succeeded" | "failed";
  isSubmitting: boolean;
  error: string | null;
};

const delay = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

export function useStrategyLab() {
  const [state, setState] = useState<StrategyLabState>({
    result: null,
    runId: null,
    status: "idle",
    isSubmitting: false,
    error: null
  });

  const submit = async (request: StrategyLabRunRequest) => {
    setState((current) => ({
      ...current,
      isSubmitting: true,
      error: null,
      status: "running",
      result: null
    }));

    try {
      const created = await createStrategyLabRun(request);
      setState((current) => ({
        ...current,
        runId: created.run_id,
        status: created.status,
        error: created.message
      }));

      if (created.status === "failed") {
        setState((current) => ({
          ...current,
          isSubmitting: false,
          status: "failed",
          error: created.message || "策略运行失败"
        }));
        return;
      }

      let status: StrategyLabState["status"] = created.status;
      for (let attempt = 0; attempt < 20 && (status === "queued" || status === "running"); attempt += 1) {
        await delay(300);
        const polled = await getStrategyLabRunStatus(created.run_id);
        status = polled.status;
        if (status === "failed") {
          setState((current) => ({
            ...current,
            isSubmitting: false,
            status,
            error: polled.message || "策略运行失败"
          }));
          return;
        }
      }

      const result = await getStrategyLabRunResult(created.run_id);
      setState({
        result,
        runId: created.run_id,
        status: "succeeded",
        isSubmitting: false,
        error: null
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "策略运行失败";
      setState({
        result: null,
        runId: null,
        status: "failed",
        isSubmitting: false,
        error: message
      });
    }
  };

  return {
    ...state,
    submit
  };
}
