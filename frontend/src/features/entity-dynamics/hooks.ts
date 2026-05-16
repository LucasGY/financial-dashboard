import { useCallback } from "react";
import { useAsyncData } from "../../lib/hooks";
import { getEntityFeed, getSourceDetail } from "./api";
import type { FeedQuery } from "./types";

export function useEntityFeed(query: FeedQuery) {
  return useAsyncData(useCallback(() => getEntityFeed(query), [query.channel, query.filter, query.entity, query.search, query.minScore]), [
    query.channel,
    query.filter,
    query.entity,
    query.search,
    query.minScore,
  ]);
}

export function useSourceDetail(slug: string | null) {
  return useAsyncData(useCallback(() => (slug ? getSourceDetail(slug) : Promise.resolve(null)), [slug]), [slug]);
}
