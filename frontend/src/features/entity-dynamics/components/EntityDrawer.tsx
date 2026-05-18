import { ArrowLeft, Calendar, ExternalLink, X } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { labelForEvent, type Language } from "../labels";
import { useSourceDetail } from "../hooks";
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

  return (
    <>
      {slug && <div className="fixed inset-0 z-40 bg-slate-900/10 backdrop-blur-sm dark:bg-black/45 lg:left-64" onClick={onClose} />}

      <div
        className={`fixed right-0 top-0 z-50 flex h-full w-full transform flex-col bg-white shadow-2xl transition-transform duration-300 ease-in-out dark:bg-slate-950 dark:text-slate-100 dark:shadow-black/50 lg:left-64 lg:w-auto ${
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

              {detail && (
                <DetailContent detail={detail} language={language} />
              )}
            </div>
          </>
        )}
      </div>
    </>
  );
}

function DetailContent({ detail, language }: { detail: SourceDetail; language: Language }) {
  const primarySources = detail.sources.filter((source) => source.source_role !== "related_discussion");
  const relatedSources = detail.sources.filter((source) => source.source_role === "related_discussion");

  return (
    <>
                  <div className="mb-4 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-400 dark:text-slate-500">
                    <span className="inline-flex items-center gap-1 font-mono">
                      <Calendar className="size-3.5" />
                      {detail.source_date}
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

                  <h1 className="mb-5 text-xl font-bold leading-snug text-slate-950 dark:text-slate-50">{getTitle(detail, language)}</h1>

                  {getSummary(detail, language) && (
                    <div className="mb-6 border-l-2 border-slate-900 bg-slate-50 px-4 py-3 text-[13px] leading-6 text-slate-700 dark:border-amber-400 dark:bg-amber-400/10 dark:text-slate-200">
                      {getSummary(detail, language)}
                    </div>
                  )}

                  {primarySources.length > 0 && <SourceSection title={language === "zh" ? "主来源" : "Primary sources"} sources={primarySources} language={language} />}
                  {relatedSources.length > 0 && <SourceSection title={language === "zh" ? "关联讨论" : "Related discussions"} sources={relatedSources} language={language} />}

                  <div className="prose prose-slate max-w-none text-[14px] leading-relaxed dark:prose-invert prose-strong:text-amber-500 dark:prose-strong:text-amber-300">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{preprocessMarkdown(detail.content)}</ReactMarkdown>
                  </div>
    </>
  );
}

function SourceSection({ title, sources, language }: { title: string; sources: IntelligenceSource[]; language: Language }) {
  return (
    <section className="mb-7">
      <h2 className="mb-3 text-sm font-bold text-slate-900 dark:text-white">{title}</h2>
      <div className="space-y-2">
        {sources.map((source) => (
          <SourceCard key={source.id} source={source} language={language} />
        ))}
      </div>
    </section>
  );
}

function SourceCard({ source, language }: { source: IntelligenceSource; language: Language }) {
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
  return (
    <div className="rounded-md border border-slate-200 p-3 dark:border-slate-800">
      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400 dark:text-slate-500">
        <span>{source.source_platform}</span>
        <span>{source.source_type}</span>
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
        <span className="font-mono">{source.source_date}</span>
        {source.source_url && (
          <a href={source.source_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-blue-500 hover:underline dark:text-amber-300">
            {language === "zh" ? "打开" : "Open"}
            <ExternalLink className="size-3" />
          </a>
        )}
      </div>
      <div className="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-100">{source.title}</div>
      {(source.raw_content || source.summary) && <p className="mt-1 text-[13px] leading-6 text-slate-600 dark:text-slate-400">{source.raw_content || source.summary}</p>}
      {source.assets.length > 0 && (
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
          {source.assets.slice(0, 6).map((asset, index) => (
            <AssetPreview key={`${String(asset.url)}-${index}`} asset={asset} />
          ))}
        </div>
      )}
    </div>
  );
}

function AssetPreview({ asset }: { asset: Record<string, unknown> }) {
  const url = typeof asset.url === "string" ? asset.url : "";
  const type = typeof asset.type === "string" ? asset.type : "image";
  if (!url) {
    return null;
  }
  if (type === "video") {
    return (
      <div className="relative overflow-hidden rounded border border-slate-200 bg-slate-950 dark:border-slate-800">
        <video src={url} controls preload="metadata" playsInline className="aspect-video w-full object-cover" />
        <span className="pointer-events-none absolute left-2 top-2 rounded bg-black/65 px-2 py-0.5 text-[10px] font-bold uppercase text-white">
          Video
        </span>
      </div>
    );
  }
  return <img src={url} alt="" className="aspect-video w-full rounded border border-slate-200 object-cover dark:border-slate-800" loading="lazy" referrerPolicy="no-referrer" />;
}
