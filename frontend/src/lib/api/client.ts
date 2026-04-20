import { ApiError, type ApiErrorPayload } from "./types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "/api/v1").replace(/\/$/, "");

const buildUrl = (path: string, params?: Record<string, string | undefined>) => {
  const url = new URL(`${API_BASE_URL}${path}`, window.location.origin);

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value) {
        url.searchParams.set(key, value);
      }
    });
  }

  return `${url.pathname}${url.search}`;
};

export async function getJson<T>(path: string, params?: Record<string, string | undefined>): Promise<T> {
  const response = await fetch(buildUrl(path, params), {
    headers: {
      Accept: "application/json"
    }
  });

  if (!response.ok) {
    let payload: ApiErrorPayload | undefined;
    try {
      payload = (await response.json()) as ApiErrorPayload;
    } catch {
      payload = undefined;
    }

    throw new ApiError(
      payload?.error?.message || `Request failed with status ${response.status}`,
      response.status,
      payload?.error?.code
    );
  }

  return (await response.json()) as T;
}
