import { getJson } from "../../lib/api/client";
import type { FeedResponse, SourceDetail } from "./types";

export const getEntityFeed = () => getJson<FeedResponse>("/entity-dynamics/feed");

export const getSourceDetail = (slug: string) =>
  getJson<SourceDetail>(`/entity-dynamics/sources/${slug}`);
