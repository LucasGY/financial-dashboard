import { ArrowLeft, Calendar, ExternalLink, Play, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { labelForEvent, type Language } from "../labels";
import { useSourceDetail } from "../hooks";
import { formatShanghaiDateTime } from "../date";
import type { IntelligenceSource, SourceDetail } from "../types";

function preprocessMarkdown(content: string): string {
  return content
    .replace(/\[\[([^\]|]+)\|([^\]]+)\]\]/g, "$2")
    .replace(/\[\[([^\]]+)\]\]/g, "$1");
}

function getTitle(detail: SourceDetail, language: Language) {
  return language === "zh" ? detail.title_zh || detail.title : detail.title || detail.title_zh;
}

function getSummary(detail: SourceDetail, language: Language) {
  const rawCandidate = language === "zh" ? detail.raw_excerpt_zh : detail.raw_excerpt;
  if (detail.display_mode === "raw" && rawCandidate) {
    return rawCandidate;
  }
  return language === "zh" ? detail.tldr_zh || detail.summary || detail.tldr_en : detail.summary || detail.tldr_en || detail.tldr_zh;
}

interface Props {
  slug: string | null;
  language: Language;
  onClose: () => void;
}

export function EntityDrawer({ slug, language, onClose }: Props) {
  const { data: detail, isLoading } = useSourceDetail(slug);
  const [lightboxUrl, setLightboxUrl] = useState<string | null>(null);

  return (
    <>
      {slug && <div className="fixed inset-0 z-40 bg-slate-900/10 backdrop-blur-sm dark:bg-black/45 lg:left-[208px] xl:left-[220px]" onClick={onClose} />}

      <div
        className={`fixed right-0 top-0 z-50 flex h-full w-full transform flex-col bg-white shadow-2xl transition-transform duration-300 ease-in-out dark:bg-slate-950 dark:text-slate-100 dark:shadow-black/50 lg:left-[208px] lg:w-auto xl:left-[220px] ${
          slug ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {slug && (
          <>
            <div className="flex shrink-0 items-start justify-between gap-4 border-b border-slate-100 px-6 py-4 dark:border-white/10">
              <div className="min-w-0 space-y-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
                >
                  <ArrowLeft className="size-4" />
                  {language === "zh" ? "返回列表" : "Back to feed"}
                </button>
                <div className="flex flex-wrap gap-1.5">
                  {detail?.entity_labels.map((tag) => (
                    <span key={tag} className="rounded bg-slate-100 px-2 py-1 text-[11px] font-bold text-slate-700 dark:bg-slate-900 dark:text-slate-300">
                      {tag}
                    </span>
                  ))}
                  {detail?.event_tags.map((tag) => (
                    <span key={tag} className="rounded border border-slate-200 px-2 py-1 text-[11px] font-semibold text-slate-500 dark:border-slate-800 dark:text-slate-400">
                      {labelForEvent(tag, language)}
                    </span>
                  ))}
                </div>
              </div>
              <button
                type="button"
                onClick={onClose}
                aria-label={language === "zh" ? "关闭详情" : "Close detail"}
                className="shrink-0 rounded-md border border-slate-200 p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900 dark:border-slate-800 dark:text-slate-400 dark:hover:bg-white/10 dark:hover:text-white"
              >
                <X className="size-5" />
              </button>
            </div>

            <div className="custom-scrollbar flex-1 overflow-y-auto p-7">
              {isLoading && !detail && <div className="py-16 text-center text-sm text-slate-400 dark:text-slate-500">{language === "zh" ? "加载中..." : "Loading..."}</div>}

              {detail && <DetailContent detail={detail} language={language} onOpenImage={setLightboxUrl} />}
            </div>
          </>
        )}
      </div>
      {lightboxUrl && <ImageLightbox url={lightboxUrl} onClose={() => setLightboxUrl(null)} />}
    </>
  );
}

function DetailContent({ detail, language, onOpenImage }: { detail: SourceDetail; language: Language; onOpenImage: (url: string) => void }) {
  const primarySources = detail.sources.filter((source) => source.source_role !== "related_discussion");
  const relatedSources = detail.sources.filter((source) => source.source_role === "related_discussion");
  const visibleAssetsBySourceId = useMemo(() => {
    const seen = new Set<string>();
    const result = new Map<string, Array<Record<string, unknown>>>();
    for (const source of [...primarySources, ...relatedSources]) {
      const visibleAssets = source.assets.filter((asset) => {
        const key = assetKey(asset);
        if (!key || seen.has(key)) {
          return false;
        }
        seen.add(key);
        return true;
      });
      result.set(source.id, visibleAssets);
    }
    return result;
  }, [primarySources, relatedSources]);

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-4 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-400 dark:text-slate-500">
        <span className="inline-flex items-center gap-1 font-mono">
          <Calendar className="size-3.5" />
          {formatShanghaiDateTime(detail.source_date)}
        </span>
        {detail.source_platform && <span>{detail.source_platform}</span>}
        {detail.source_type && <span>{detail.source_type}</span>}
        <span>{detail.source_count} {language === "zh" ? "来源" : "sources"}</span>
        {detail.source_url && (
          <a href={detail.source_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-blue-500 hover:underline dark:text-amber-300">
            {language === "zh" ? "原始来源" : "Original source"}
            <ExternalLink className="size-3" />
          </a>
        )}
      </div>

      <h1 className="mb-4 text-2xl font-bold leading-snug text-slate-950 dark:text-slate-50">{getTitle(detail, language)}</h1>

      {getSummary(detail, language) && (
        <div className="mb-7 rounded-md border-l-2 border-slate-900 bg-slate-50 px-4 py-3 text-sm leading-7 text-slate-700 dark:border-amber-400 dark:bg-amber-400/10 dark:text-slate-200">
          {getSummary(detail, language)}
        </div>
      )}

      {detail.artifact?.type === "html" && <HtmlArtifactFrame title={detail.artifact.title || getTitle(detail, language)} url={detail.artifact.url} language={language} />}

      {primarySources.length > 0 && <SourceSection title={language === "zh" ? "主来源" : "Primary sources"} sources={primarySources} visibleAssetsBySourceId={visibleAssetsBySourceId} language={language} onOpenImage={onOpenImage} />}
      {relatedSources.length > 0 && <SourceSection title={language === "zh" ? "关联讨论" : "Related discussions"} sources={relatedSources} visibleAssetsBySourceId={visibleAssetsBySourceId} language={language} onOpenImage={onOpenImage} />}

      {detail.sources.length === 0 && detail.content && !detail.artifact && (
        <div className="prose prose-slate max-w-none text-[14px] leading-relaxed dark:prose-invert prose-strong:text-amber-500 dark:prose-strong:text-amber-300">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{preprocessMarkdown(detail.content)}</ReactMarkdown>
        </div>
      )}
    </div>
  );
}

function HtmlArtifactFrame({ title, url, language }: { title: string; url: string; language: Language }) {
  return (
    <section className="mb-7 overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900/60">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-4 py-3 dark:border-slate-800">
        <h2 className="text-sm font-bold text-slate-900 dark:text-white">{language === "zh" ? "HTML 分析图" : "HTML artifact"}</h2>
        <a href={url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-xs font-semibold text-blue-500 hover:underline dark:text-amber-300">
          {language === "zh" ? "全页打开" : "Open full page"}
          <ExternalLink className="size-3" />
        </a>
      </div>
      <iframe
        src={url}
        title={title}
        loading="lazy"
        sandbox="allow-scripts allow-popups allow-popups-to-escape-sandbox"
        className="h-[78vh] min-h-[620px] w-full bg-white"
      />
    </section>
  );
}

function SourceSection({
  title,
  sources,
  visibleAssetsBySourceId,
  language,
  onOpenImage,
}: {
  title: string;
  sources: IntelligenceSource[];
  visibleAssetsBySourceId: Map<string, Array<Record<string, unknown>>>;
  language: Language;
  onOpenImage: (url: string) => void;
}) {
  return (
    <section className="mb-7">
      <h2 className="mb-3 text-sm font-bold text-slate-900 dark:text-white">{title}</h2>
      <div className="grid gap-3">
        {sources.map((source) => (
          <SourceCard key={source.id} source={source} visibleAssets={visibleAssetsBySourceId.get(source.id) ?? []} language={language} onOpenImage={onOpenImage} />
        ))}
      </div>
    </section>
  );
}

function SourceCard({
  source,
  visibleAssets,
  language,
  onOpenImage,
}: {
  source: IntelligenceSource;
  visibleAssets: Array<Record<string, unknown>>;
  language: Language;
  onOpenImage: (url: string) => void;
}) {
  const relationship = source.quoted_url
    ? language === "zh"
      ? "引用"
      : "Quote"
    : source.reposted_url
      ? language === "zh"
        ? "转帖"
        : "Repost"
      : source.reply_to_url
        ? language === "zh"
          ? "回复"
          : "Reply"
        : null;
  const sourceTitle = language === "zh" ? source.title_zh || source.title : source.title_en || source.title;
  const sourceBody =
    language === "zh"
      ? source.raw_content_zh || source.summary_zh || source.raw_content || source.summary
      : source.raw_content_en || source.summary_en || source.raw_content || source.summary;
  return (
    <article className="rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400 dark:text-slate-500">
        {source.source_platform && <span>{source.source_platform}</span>}
        {source.source_type && <span>{source.source_type}</span>}
        <span className="rounded bg-slate-100 px-1.5 py-0.5 font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
          {source.source_role === "related_discussion" ? (language === "zh" ? "讨论" : "Discussion") : language === "zh" ? "主来源" : "Primary"}
        </span>
        {relationship && <span>{relationship}</span>}
        {source.author_name && (
          <span className="inline-flex items-center gap-1.5">
            {source.author_avatar_url && (
              <img
                src={source.author_avatar_url}
                alt=""
                className="size-4 rounded-full bg-slate-200 object-cover dark:bg-slate-700"
                loading="lazy"
                referrerPolicy="no-referrer"
              />
            )}
            {source.author_name}
          </span>
        )}
        <span className="font-mono">{formatShanghaiDateTime(source.source_date)}</span>
        {source.source_url && (
          <a href={source.source_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-blue-500 hover:underline dark:text-amber-300">
            {language === "zh" ? "打开" : "Open"}
            <ExternalLink className="size-3" />
          </a>
        )}
      </div>
      <div className="mt-3 text-base font-semibold leading-snug text-slate-900 dark:text-slate-100">{sourceTitle}</div>
      {sourceBody && <p className="mt-2 line-clamp-4 text-sm leading-7 text-slate-600 dark:text-slate-400">{sourceBody}</p>}
      {visibleAssets.length > 0 && (
        <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {visibleAssets.slice(0, 6).map((asset, index) => (
            <AssetPreview key={`${String(asset.url)}-${index}`} asset={asset} sourceUrl={source.source_url} onOpenImage={onOpenImage} />
          ))}
        </div>
      )}
    </article>
  );
}

function AssetPreview({ asset, sourceUrl, onOpenImage }: { asset: Record<string, unknown>; sourceUrl: string | null; onOpenImage: (url: string) => void }) {
  const url = typeof asset.url === "string" ? asset.url : "";
  const thumbnailUrl = typeof asset.thumbnail_url === "string" ? asset.thumbnail_url : "";
  const type = typeof asset.type === "string" ? asset.type : "image";
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
        onClick={() => window.open(openTarget, "_blank", "noopener,noreferrer")}
        className="group relative overflow-hidden rounded border border-slate-200 bg-slate-950 text-left dark:border-slate-800"
      >
        {previewUrl ? (
          <img src={previewUrl} alt="" className="aspect-video w-full object-cover opacity-95 transition-transform group-hover:scale-[1.02]" loading="lazy" referrerPolicy="no-referrer" />
        ) : (
          <VideoFrame url={videoPreviewUrl} />
        )}
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
      onClick={() => onOpenImage(url)}
      className="overflow-hidden rounded border border-slate-200 bg-slate-100 text-left dark:border-slate-800 dark:bg-slate-900"
    >
      <img src={url} alt="" className="aspect-video w-full object-cover transition-transform hover:scale-[1.02]" loading="lazy" referrerPolicy="no-referrer" />
    </button>
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
      <img src={url} alt="" className="max-h-[92vh] max-w-[92vw] rounded-md object-contain shadow-2xl" referrerPolicy="no-referrer" onClick={(event) => event.stopPropagation()} />
    </div>
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
