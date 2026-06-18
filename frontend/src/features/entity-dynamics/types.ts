export type Channel = "daily" | "ai" | "finance" | "deep_dive";
export type SourceKind = "feed" | "manual" | "digest";

export interface FeedQuery {
  channel: Channel;
  filter?: string;
  entity?: string;
  search?: string;
  minScore?: number;
  limit?: number;
  cursor?: string | null;
}

export interface FeedItem {
  id: string;
  slug: string;
  channel: Channel;
  domain: string;
  source_kind: SourceKind;
  source_platform: string | null;
  source_type: string | null;
  source_role: string;
  source_name: string | null;
  author_name: string | null;
  author_avatar_url: string | null;
  source_date: string;
  title: string;
  title_zh: string;
  summary: string;
  tldr_zh: string;
  tldr_en: string;
  raw_excerpt: string;
  raw_excerpt_zh: string;
  display_mode: string;
  assets: Array<Record<string, unknown>>;
  entity_ids: string[];
  entity_labels: string[];
  event_tags: string[];
  topic_tags: string[];
  importance_score: number | null;
  source_count: number;
  has_related_discussions: boolean;
  is_favorited: boolean;
  source_url: string | null;
  status: string;
}

export interface FeedResponse {
  items: FeedItem[];
  next_cursor: string | null;
  has_more: boolean;
}

export interface IntelligenceSource {
  id: string;
  source_name: string | null;
  source_platform: string | null;
  source_type: string | null;
  source_role: string;
  original_url: string | null;
  quoted_url: string | null;
  reposted_url: string | null;
  reply_to_url: string | null;
  assets: Array<Record<string, unknown>>;
  extraction_status: string | null;
  author_name: string | null;
  author_avatar_url: string | null;
  source_date: string;
  title: string;
  title_en: string;
  title_zh: string;
  summary: string;
  summary_en: string;
  summary_zh: string;
  source_url: string | null;
  raw_content: string;
  raw_content_en: string;
  raw_content_zh: string;
}

export interface IntelligenceArtifact {
  type: "html";
  title: string;
  url: string;
}

export interface SourceDetail extends FeedItem {
  content: string;
  sources: IntelligenceSource[];
  artifact: IntelligenceArtifact | null;
}

export interface FavoriteResponse {
  slug: string;
  is_favorited: boolean;
}
