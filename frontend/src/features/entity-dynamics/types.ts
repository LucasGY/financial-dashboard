export type ContentType = "podcast" | "article" | "news" | "release" | "tweet" | "research";
export type FrontendCategory = "mag7" | "ai" | "content";

export interface FeedItem {
  slug: string;
  source_date: string;
  content_type: ContentType;
  frontend_category: FrontendCategory;
  entity_tags: string[];
  title: string;
  title_zh: string;
  tldr_zh: string;
  tldr_en: string;
  source_platform: string | null;
  source_url: string | null;
}

export interface FeedResponse {
  items: FeedItem[];
}

export interface SourceDetail extends FeedItem {
  content: string;
}
