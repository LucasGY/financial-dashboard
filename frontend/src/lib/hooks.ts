import { useEffect, useState } from "react";

type AsyncState<T> = {
  data: T | null;
  error: Error | null;
  isLoading: boolean;
};

export function useAsyncData<T>(loader: () => Promise<T>, deps: ReadonlyArray<unknown>): AsyncState<T> {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    error: null,
    isLoading: true
  });

  useEffect(() => {
    let active = true;

    setState((current) => ({
      data: current.data,
      error: null,
      isLoading: true
    }));

    loader()
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
  }, deps);

  return state;
}
