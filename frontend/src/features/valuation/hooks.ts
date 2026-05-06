import { startTransition, useEffect, useState } from "react";
import { getValuationTimeline } from "./api";
import type { ValuationTimelineResponse, ValuationWindow } from "./types";

type ValuationState = {
  data: ValuationTimelineResponse | null;
  error: Error | null;
  isLoading: boolean;
};

export function useValuationTimeline(index: "SPX" | "NDX", window: ValuationWindow) {
  const [state, setState] = useState<ValuationState>({
    data: null,
    error: null,
    isLoading: true
  });

  useEffect(() => {
    let active = true;

    startTransition(() => {
      setState((current) => ({
        data: current.data,
        error: null,
        isLoading: true
      }));
    });

    getValuationTimeline(index, window)
      .then((data) => {
        if (!active) {
          return;
        }

        setState({
          data,
          error: null,
          isLoading: false
        });
      })
      .catch((error: Error) => {
        if (!active) {
          return;
        }

        setState({
          data: null,
          error,
          isLoading: false
        });
      });

    return () => {
      active = false;
    };
  }, [index, window]);

  return state;
}
