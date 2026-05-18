import { ExternalLink, Layers } from "lucide-react";
import { useMemo, useState } from "react";
import type React from "react";
import { labelForEvent, type Language } from "../labels";
import { useEntityFeed } from "../hooks";
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
  const { data, isLoading, error } = useEntityFeed({ channel, filter, entity, search, minScore });
  const items = data?.items ?? [];
  const groupedItems = useMemo(() => groupByDate(items), [items]);
  const dates = Object.keys(groupedItems);

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
    <div className="pb-8">
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
                />
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

function FeedCard({ item, isSelected, language, onClick }: { item: FeedItem; isSelected: boolean; language: Language; onClick: () => void }) {
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
        {item.importance_score !== null && (
          <span
            className={`shrink-0 rounded-md border px-2 py-1 text-xs font-bold leading-none ${
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

      {item.assets.length > 0 && (
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
          {item.assets.slice(0, 3).map((asset, index) => (
            <CardAssetPreview key={`${String(asset.url)}-${index}`} asset={asset} />
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

function CardAssetPreview({ asset }: { asset: Record<string, unknown> }) {
  const url = typeof asset.url === "string" ? asset.url : "";
  const type = typeof asset.type === "string" ? asset.type : "image";
  if (!url) {
    return null;
  }
  if (type === "video") {
    return (
      <div className="relative overflow-hidden rounded border border-slate-200 bg-slate-950 dark:border-slate-800">
        <video
          src={url}
          muted
          playsInline
          controls
          preload="metadata"
          className="aspect-video w-full object-cover"
        />
        <span className="pointer-events-none absolute left-2 top-2 rounded bg-black/65 px-2 py-0.5 text-[10px] font-bold uppercase text-white">
          Video
        </span>
      </div>
    );
  }
  return (
    <img
      src={url}
      alt=""
      className="aspect-video w-full rounded border border-slate-200 object-cover dark:border-slate-800"
      loading="lazy"
      referrerPolicy="no-referrer"
    />
  );
}
