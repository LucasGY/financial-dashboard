import { ExternalLink, Layers, Play, Star, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import type React from "react";
import { labelForEvent, type Language } from "../labels";
import { usePagedEntityFeed } from "../hooks";
import { setSourceFavorite } from "../api";
import type { Channel, FeedItem } from "../types";

interface Props {
  channel: Channel;
  filter: string;
  entity: string;
  search: string;
  minScore: number;
  language: Language;
  onSelectItem: (slug: string) => void;
  selectedSlug: string | null;
}

function groupByDate(items: FeedItem[]) {
  return items.reduce<Record<string, FeedItem[]>>((groups, item) => {
    const date = item.source_date.slice(0, 10) || "Unknown";
    groups[date] = groups[date] ?? [];
    groups[date].push(item);
    return groups;
  }, {});
}

function formatTime(date: string) {
  const time = date.slice(11, 16);
  return time || date;
}

export function EntityFeed({ channel, filter, entity, search, minScore, language, onSelectItem, selectedSlug }: Props) {
  const { data, isLoading, isLoadingMore, error, loadMore, updateItem, removeItem } = usePagedEntityFeed({ channel, filter, entity, search, minScore, limit: 35 });
  const [lightboxUrl, setLightboxUrl] = useState<string | null>(null);
  const [favoriteError, setFavoriteError] = useState<string | null>(null);
  const loadMoreRef = useRef<HTMLDivElement | null>(null);
  const autoLoadEnabledRef = useRef(true);
  const autoLoadScrollArmedRef = useRef(false);
  const autoLoadSuppressedUntilRef = useRef(0);
  const items = data?.items ?? [];
  const groupedItems = useMemo(() => groupByDate(items), [items]);
  const dates = Object.keys(groupedItems);

  useEffect(() => {
    autoLoadEnabledRef.current = true;
    autoLoadScrollArmedRef.current = false;
  }, [channel, filter, entity, search, minScore]);

  useEffect(() => {
    const markAutoLoadReady = () => {
      if (Date.now() < autoLoadSuppressedUntilRef.current) {
        return;
      }
      autoLoadEnabledRef.current = true;
      autoLoadScrollArmedRef.current = true;
    };
    window.addEventListener("scroll", markAutoLoadReady, { passive: true });
    return () => window.removeEventListener("scroll", markAutoLoadReady);
  }, []);

  useEffect(() => {
    const node = loadMoreRef.current;
    if (!node || !data.has_more) {
      return;
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) {
          return;
        }
        if (
          !autoLoadEnabledRef.current ||
          !autoLoadScrollArmedRef.current ||
          Date.now() < autoLoadSuppressedUntilRef.current ||
          isLoadingMore
        ) {
          return;
        }
        autoLoadEnabledRef.current = false;
        autoLoadScrollArmedRef.current = false;
        autoLoadSuppressedUntilRef.current = Date.now() + 3000;
        loadMore();
      },
      { rootMargin: "500px" }
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [data.has_more, isLoadingMore, loadMore]);

  const handleLoadMore = () => {
    autoLoadEnabledRef.current = false;
    autoLoadScrollArmedRef.current = false;
    autoLoadSuppressedUntilRef.current = Date.now() + 3000;
    loadMore();
  };

  const handleToggleFavorite = async (item: FeedItem) => {
    const nextValue = !item.is_favorited;
    setFavoriteError(null);
    updateItem(item.slug, (current) => ({ ...current, is_favorited: nextValue }));
    try {
      await setSourceFavorite(item.slug, nextValue);
      if (filter === "favorite" && !nextValue) {
        removeItem(item.slug);
      }
    } catch {
      updateItem(item.slug, (current) => ({ ...current, is_favorited: !nextValue }));
      setFavoriteError(language === "zh" ? "收藏失败，请稍后重试" : "Failed to update saved state");
    }
  };

  if (isLoading) {
    return <div className="py-16 text-center text-sm text-slate-400 dark:text-slate-500">{language === "zh" ? "加载中..." : "Loading..."}</div>;
  }

  if (error) {
    return <div className="py-16 text-center text-sm text-red-500 dark:text-red-300">{language === "zh" ? "加载失败，请检查后端服务" : "Failed to load. Check the backend service."}</div>;
  }

  if (dates.length === 0) {
    return <div className="py-16 text-center text-sm text-slate-400 dark:text-slate-500">{language === "zh" ? "没有找到相关内容" : "No matching items"}</div>;
  }

  return (
    <>
      <div className="pb-8">
        {favoriteError && <div className="mb-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-600 dark:border-red-400/30 dark:bg-red-400/10 dark:text-red-200">{favoriteError}</div>}
        {dates.map((date) => (
          <section key={date} className="border-b border-slate-200 py-5 last:border-b-0 dark:border-slate-800">
            <div className="mb-3 text-xs font-semibold text-slate-400 dark:text-slate-500">{date}</div>
            <div className="space-y-2">
              {groupedItems[date].map((item) => (
                <div key={item.id} className="grid gap-3 md:grid-cols-[64px_22px_minmax(0,1fr)]">
                  <div className="pt-4 text-xs font-mono text-slate-400 dark:text-slate-500">{formatTime(item.source_date)}</div>
                  <div className="relative hidden md:block">
                    <div className="absolute left-1/2 top-0 h-full w-px -translate-x-1/2 bg-slate-200 dark:bg-slate-800" />
                    <div className="absolute left-1/2 top-5 size-2.5 -translate-x-1/2 rounded-full border-2 border-white bg-slate-400 dark:border-slate-950 dark:bg-amber-400" />
                  </div>
                  <FeedCard
                    item={item}
                    isSelected={item.slug === selectedSlug}
                    language={language}
                    onClick={() => onSelectItem(item.slug)}
                    onOpenImage={setLightboxUrl}
                    onToggleFavorite={() => handleToggleFavorite(item)}
                  />
                </div>
              ))}
            </div>
          </section>
        ))}
        <div ref={loadMoreRef} className="pt-5 text-center">
          {data.has_more ? (
            <button
              type="button"
              onClick={handleLoadMore}
              disabled={isLoadingMore}
              className="rounded-md border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              {isLoadingMore ? (language === "zh" ? "加载中..." : "Loading...") : language === "zh" ? "加载更早日期" : "Load older dates"}
            </button>
          ) : (
            <div className="text-xs text-slate-400 dark:text-slate-500">{language === "zh" ? "没有更早内容" : "No older items"}</div>
          )}
        </div>
      </div>
      {lightboxUrl && <ImageLightbox url={lightboxUrl} onClose={() => setLightboxUrl(null)} />}
    </>
  );
}

function ImageLightbox({ url, onClose }: { url: string; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-[70] grid place-items-center bg-black/85 p-4" onClick={onClose}>
      <button
        type="button"
        aria-label="Close image"
        onClick={onClose}
        className="absolute right-4 top-4 rounded-md border border-white/20 bg-black/40 p-2 text-white transition-colors hover:bg-white/10"
      >
        <X className="size-5" />
      </button>
      <img
        src={url}
        alt=""
        className="max-h-[92vh] max-w-[92vw] rounded-md object-contain shadow-2xl"
        referrerPolicy="no-referrer"
        onClick={(event) => event.stopPropagation()}
      />
    </div>
  );
}

function FeedCard({
  item,
  isSelected,
  language,
  onClick,
  onOpenImage,
  onToggleFavorite,
}: {
  item: FeedItem;
  isSelected: boolean;
  language: Language;
  onClick: () => void;
  onOpenImage: (url: string) => void;
  onToggleFavorite: () => void;
}) {
  const title = language === "zh" ? item.title_zh || item.title : item.title || item.title_zh;
  const rawCandidate = language === "zh" ? item.raw_excerpt_zh : item.raw_excerpt;
  const summaryCandidate =
    item.display_mode === "raw" && rawCandidate
      ? rawCandidate
      : language === "zh"
        ? item.tldr_zh || item.summary || item.tldr_en
        : item.summary || item.tldr_en || item.tldr_zh;
  const summary = summaryCandidate.trim().toLowerCase() === title.trim().toLowerCase() ? "" : summaryCandidate;
  const platformLabel = item.source_platform;
  const showAuthorAvatar = item.source_platform === "X" && item.author_name;
  const shouldOpenOriginal = item.source_count === 1 && !item.has_related_discussions && item.source_role === "primary" && Boolean(item.source_url);
  const visibleAssets = cardAssets(item);

  const openOriginalOrDetail = () => {
    if (shouldOpenOriginal && item.source_url) {
      window.open(item.source_url, "_blank", "noopener,noreferrer");
      return;
    }
    onClick();
  };

  const handleSourceClick = (event: React.MouseEvent<HTMLButtonElement | HTMLAnchorElement>) => {
    event.stopPropagation();
    if (shouldOpenOriginal && item.source_url) {
      window.open(item.source_url, "_blank", "noopener,noreferrer");
      return;
    }
    onClick();
  };

  return (
    <article
      role="button"
      tabIndex={0}
      onClick={openOriginalOrDetail}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openOriginalOrDetail();
        }
      }}
      className={`block w-full cursor-pointer rounded-md border px-4 py-3 text-left transition-colors ${
        isSelected
          ? "border-slate-900 bg-slate-900 text-white dark:border-amber-400 dark:bg-amber-400/10 dark:text-slate-100"
          : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-slate-700 dark:hover:bg-slate-900/80"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-400 dark:text-slate-500">
          {showAuthorAvatar && (
            <span className="inline-flex min-w-0 items-center gap-1.5">
              <AuthorAvatar authorName={item.author_name} avatarUrl={item.author_avatar_url} />
              <span className="truncate">{item.author_name}</span>
            </span>
          )}
          {platformLabel && <span>{platformLabel}</span>}
          <button type="button" onClick={handleSourceClick} className="inline-flex items-center gap-1 transition-colors hover:text-slate-900 dark:hover:text-white">
            <Layers className="size-3" />
            {item.source_count} {language === "zh" ? "来源" : "sources"}
          </button>
          {item.source_url && <ExternalLink className="size-3" />}
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          <button
            type="button"
            aria-label={item.is_favorited ? (language === "zh" ? "取消收藏" : "Unsave") : language === "zh" ? "收藏" : "Save"}
            title={item.is_favorited ? (language === "zh" ? "取消收藏" : "Unsave") : language === "zh" ? "收藏" : "Save"}
            onClick={(event) => {
              event.stopPropagation();
              onToggleFavorite();
            }}
            className={`grid size-7 place-items-center rounded-md border transition-colors ${
              item.is_favorited
                ? "border-amber-300 bg-amber-100 text-amber-700 dark:border-amber-400/40 dark:bg-amber-400/15 dark:text-amber-200"
                : "border-slate-200 bg-slate-50 text-slate-400 hover:text-amber-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-500 dark:hover:text-amber-300"
            }`}
          >
            <Star className={`size-3.5 ${item.is_favorited ? "fill-current" : ""}`} />
          </button>
          {item.importance_score !== null && (
            <span
              className={`rounded-md border px-2 py-1 text-xs font-bold leading-none ${
                item.importance_score >= 80
                  ? "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-400/30 dark:bg-emerald-400/15 dark:text-emerald-200"
                  : item.importance_score >= 60
                    ? "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-400/30 dark:bg-amber-400/15 dark:text-amber-200"
                    : "border-slate-200 bg-slate-50 text-slate-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400"
              }`}
            >
              {item.importance_score}
            </span>
          )}
        </div>
      </div>

      <button
        type="button"
        onClick={(event) => {
          event.stopPropagation();
          openOriginalOrDetail();
        }}
        className="mt-2 block w-full text-left"
      >
        <h3 className={`text-[15px] font-bold leading-snug ${isSelected ? "" : "text-slate-900 dark:text-slate-100"}`}>
          {title}
        </h3>
        {summary && (
          <p className={`mt-1 line-clamp-2 text-[13px] leading-6 ${isSelected ? "text-slate-200 dark:text-slate-300" : "text-slate-600 dark:text-slate-400"}`}>
            {summary}
          </p>
        )}
      </button>

      {visibleAssets.length > 0 && (
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
          {visibleAssets.map((asset, index) => (
            <CardAssetPreview key={`${String(asset.url)}-${index}`} asset={asset} sourceUrl={item.source_url} onOpenImage={onOpenImage} />
          ))}
        </div>
      )}

      <div className="mt-3 flex flex-wrap gap-1.5">
        {item.entity_labels.map((tag) => (
          <span
            key={tag}
            className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${
              isSelected
                ? "bg-white/10 text-white dark:bg-amber-400/15 dark:text-amber-200"
                : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
            }`}
          >
            {tag}
          </span>
        ))}
        {item.event_tags.map((tag) => (
          <span
            key={tag}
            className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold ${
              isSelected
                ? "border-white/20 text-slate-100 dark:border-amber-400/30 dark:text-amber-200"
                : "border-slate-200 text-slate-500 dark:border-slate-700 dark:text-slate-400"
            }`}
          >
            {labelForEvent(tag, language)}
          </span>
        ))}
      </div>
    </article>
  );
}

function AuthorAvatar({ authorName, avatarUrl }: { authorName: string | null; avatarUrl: string | null }) {
  const [failed, setFailed] = useState(false);
  if (avatarUrl && !failed) {
    return (
      <img
        src={avatarUrl}
        alt=""
        className="size-4 shrink-0 rounded-full bg-slate-200 object-cover dark:bg-slate-700"
        loading="lazy"
        referrerPolicy="no-referrer"
        onError={() => setFailed(true)}
      />
    );
  }
  return (
    <span className="grid size-4 shrink-0 place-items-center rounded-full bg-slate-200 text-[9px] font-bold text-slate-600 dark:bg-slate-700 dark:text-slate-200">
      {avatarInitial(authorName)}
    </span>
  );
}

function avatarInitial(authorName: string | null) {
  const normalized = (authorName || "").replace(/^@/, "").trim();
  return (normalized[0] || "X").toUpperCase();
}

function CardAssetPreview({
  asset,
  sourceUrl,
  onOpenImage,
}: {
  asset: Record<string, unknown>;
  sourceUrl: string | null;
  onOpenImage: (url: string) => void;
}) {
  const [isVisible, setIsVisible] = useState(false);
  const previewRef = useRef<HTMLDivElement | null>(null);
  const url = typeof asset.url === "string" ? asset.url : "";
  const thumbnailUrl = typeof asset.thumbnail_url === "string" ? asset.thumbnail_url : "";
  const type = typeof asset.type === "string" ? asset.type : "image";
  useEffect(() => {
    const node = previewRef.current;
    if (!node || isVisible) {
      return;
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "300px" }
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [isVisible]);
  if (!url) {
    return null;
  }
  if (type === "video") {
    const previewUrl = thumbnailUrl || (isImageUrl(url) ? url : "");
    const videoPreviewUrl = proxiedVideoUrl(url);
    const openTarget = sourceUrl || url;
    return (
      <button
        type="button"
        onClick={(event) => {
          event.stopPropagation();
          window.open(openTarget, "_blank", "noopener,noreferrer");
        }}
        className="group relative overflow-hidden rounded border border-slate-200 bg-slate-950 text-left dark:border-slate-800"
      >
        <div ref={previewRef}>
        {!isVisible ? (
          <div className="aspect-video w-full bg-slate-900" />
        ) : previewUrl ? (
          <img src={previewUrl} alt="" className="aspect-video w-full object-cover opacity-95 transition-transform group-hover:scale-[1.02]" loading="lazy" referrerPolicy="no-referrer" />
        ) : (
          <VideoFrame url={videoPreviewUrl} />
        )}
        </div>
        <span className="absolute inset-0 grid place-items-center bg-black/10 transition-colors group-hover:bg-black/20">
          <span className="grid size-10 place-items-center rounded-full bg-black/65 text-white shadow-lg">
            <Play className="ml-0.5 size-5 fill-current" />
          </span>
        </span>
      </button>
    );
  }
  return (
    <button
      type="button"
      onClick={(event) => {
        event.stopPropagation();
        onOpenImage(url);
      }}
      className="overflow-hidden rounded border border-slate-200 bg-slate-100 text-left dark:border-slate-800 dark:bg-slate-900"
    >
      <div ref={previewRef}>
        {isVisible ? (
          <img
            src={url}
            alt=""
            className="aspect-video w-full object-cover transition-transform hover:scale-[1.02]"
            loading="lazy"
            referrerPolicy="no-referrer"
          />
        ) : (
          <div className="aspect-video w-full bg-slate-100 dark:bg-slate-900" />
        )}
      </div>
    </button>
  );
}

function isImageUrl(url: string) {
  return /\.(png|jpe?g|webp|gif)(\?|#|$)/i.test(url);
}

function VideoFrame({ url }: { url: string }) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [frameUrl, setFrameUrl] = useState<string>("");
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setFrameUrl("");
    setFailed(false);
  }, [url]);

  if (frameUrl) {
    return <img src={frameUrl} alt="" className="aspect-video w-full object-cover opacity-95 transition-transform group-hover:scale-[1.02]" />;
  }

  return (
    <>
      <div className="grid aspect-video w-full place-items-center bg-slate-900 text-xs font-semibold uppercase tracking-wide text-slate-500">
        {failed ? "Video" : ""}
      </div>
      <video
        ref={videoRef}
        src={url}
        crossOrigin="anonymous"
        muted
        playsInline
        preload="auto"
        className="sr-only"
        onLoadedMetadata={(event) => {
          const video = event.currentTarget;
          video.currentTime = Number.isFinite(video.duration) ? Math.min(1.2, Math.max(0.2, video.duration * 0.25)) : 0.8;
        }}
        onSeeked={(event) => {
          const video = event.currentTarget;
          if (!video.videoWidth || !video.videoHeight) {
            setFailed(true);
            return;
          }
          const canvas = document.createElement("canvas");
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          const context = canvas.getContext("2d");
          if (!context) {
            setFailed(true);
            return;
          }
          context.drawImage(video, 0, 0, canvas.width, canvas.height);
          setFrameUrl(canvas.toDataURL("image/jpeg", 0.82));
        }}
        onError={() => setFailed(true)}
      />
    </>
  );
}

function uniqueAssets(assets: Array<Record<string, unknown>>) {
  const seen = new Set<string>();
  return assets.filter((asset) => {
    const key = assetKey(asset);
    if (!key || seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

function cardAssets(item: FeedItem) {
  const assets = uniqueAssets(item.assets);
  if (item.source_platform === "X" && assets.length > 1) {
    return assets.slice(0, 1);
  }
  return assets.slice(0, 3);
}

function assetKey(asset: Record<string, unknown>) {
  const type = typeof asset.type === "string" ? asset.type : "image";
  const url = typeof asset.url === "string" ? asset.url : "";
  return url ? `${type}:${canonicalMediaUrl(url)}` : "";
}

function canonicalMediaUrl(url: string) {
  const tweetVideoMatch = url.match(/(?:amplify_video|ext_tw_video)\/(\d+)\//);
  if (tweetVideoMatch) {
    return `x-video:${tweetVideoMatch[1]}`;
  }
  return url.split("?")[0];
}

function proxiedVideoUrl(url: string) {
  try {
    const parsed = new URL(url);
    if (parsed.hostname === "video.twimg.com" || parsed.hostname === "video.x.com") {
      return `/api/v1/entity-dynamics/media/video?url=${encodeURIComponent(url)}`;
    }
  } catch {
    return url;
  }
  return url;
}
