import { getJson, postJson } from "../../lib/api/client";
import type { FavoriteResponse, FeedQuery, FeedResponse, SourceDetail } from "./types";

export const getEntityFeed = ({ channel, filter = "all", entity = "all", search = "", minScore = 0, limit = 35, cursor = null }: FeedQuery) => {
  const params = new URLSearchParams({ channel, filter });
  if (entity !== "all") params.set("entity", entity);
  if (search.trim()) params.set("search", search.trim());
  if (minScore > 0) params.set("min_score", String(minScore));
  params.set("limit", String(limit));
  if (cursor) params.set("cursor", cursor);
  return getJson<FeedResponse>(`/entity-dynamics/feed?${params.toString()}`);
};

export const getSourceDetail = (slug: string) =>
  getJson<SourceDetail>(`/entity-dynamics/sources/${encodeURIComponent(slug)}`);

export const setSourceFavorite = (slug: string, isFavorited: boolean) =>
  postJson<FavoriteResponse, { is_favorited: boolean }>(`/entity-dynamics/sources/${encodeURIComponent(slug)}/favorite`, {
    is_favorited: isFavorited,
  });
