import { useCallback, useEffect, useRef, useState } from "react";
import { useAsyncData } from "../../lib/hooks";
import { getEntityFeed, getSourceDetail } from "./api";
import type { FeedItem, FeedQuery } from "./types";

export function useEntityFeed(query: FeedQuery) {
  return useAsyncData(useCallback(() => getEntityFeed(query), [query.channel, query.filter, query.entity, query.search, query.minScore]), [
    query.channel,
    query.filter,
    query.entity,
    query.search,
    query.minScore,
  ]);
}

export function usePagedEntityFeed(query: FeedQuery) {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const isLoadingMoreRef = useRef(false);
  const lastLoadStartedAtRef = useRef(0);
  const queryKey = [query.channel, query.filter, query.entity, query.search, query.minScore].join("|");

  useEffect(() => {
    let active = true;
    isLoadingMoreRef.current = false;
    lastLoadStartedAtRef.current = 0;
    setIsLoading(true);
    setError(null);
    getEntityFeed({ ...query, limit: query.limit ?? 35, cursor: null })
      .then((response) => {
        if (!active) return;
        setItems(response.items);
        setNextCursor(response.next_cursor);
        setHasMore(response.has_more);
        setIsLoading(false);
      })
      .catch((err: Error) => {
        if (!active) return;
        setError(err);
        setItems([]);
        setNextCursor(null);
        setHasMore(false);
        setIsLoading(false);
      });
    return () => {
      active = false;
    };
  }, [queryKey, query.limit]);

  const loadMore = useCallback(() => {
    const now = Date.now();
    if (!nextCursor || isLoadingMoreRef.current || now - lastLoadStartedAtRef.current < 3000) return;
    isLoadingMoreRef.current = true;
    lastLoadStartedAtRef.current = now;
    setIsLoadingMore(true);
    setError(null);
    getEntityFeed({ ...query, limit: query.limit ?? 35, cursor: nextCursor })
      .then((response) => {
        setItems((current) => [...current, ...response.items]);
        setNextCursor(response.next_cursor);
        setHasMore(response.has_more);
        isLoadingMoreRef.current = false;
        setIsLoadingMore(false);
      })
      .catch((err: Error) => {
        setError(err);
        isLoadingMoreRef.current = false;
        setIsLoadingMore(false);
      });
  }, [nextCursor, query]);

  const updateItem = useCallback((slug: string, updater: (item: FeedItem) => FeedItem) => {
    setItems((current) => current.map((item) => (item.slug === slug ? updater(item) : item)));
  }, []);

  const removeItem = useCallback((slug: string) => {
    setItems((current) => current.filter((item) => item.slug !== slug));
  }, []);

  return { data: { items, next_cursor: nextCursor, has_more: hasMore }, isLoading, isLoadingMore, error, loadMore, updateItem, removeItem };
}

export function useSourceDetail(slug: string | null) {
  return useAsyncData(useCallback(() => (slug ? getSourceDetail(slug) : Promise.resolve(null)), [slug]), [slug]);
}
