import { startTransition, useEffect, useState } from "react";
import { getPriceAttribution, getValuationTimeline } from "./api";
import type { AttributionTag, PriceAttributionResponse, ValuationTimelineResponse, ValuationWindow } from "./types";

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

type AttributionState = {
  data: PriceAttributionResponse | null;
  error: Error | null;
  isLoading: boolean;
};

export function usePriceAttribution(index: "SPX" | "NDX", tag: AttributionTag) {
  const [state, setState] = useState<AttributionState>({
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

    getPriceAttribution(index, tag)
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
  }, [index, tag]);

  return state;
}
