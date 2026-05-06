import { Calendar, ExternalLink, X } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useLanguage } from "../../../app/language";
import { useSourceDetail } from "../hooks";
import type { SourceDetail } from "../types";

function preprocessMarkdown(content: string): string {
  return content
    .replace(/\[\[([^\]|]+)\|([^\]]+)\]\]/g, "$2")
    .replace(/\[\[([^\]]+)\]\]/g, "$1");
}

function getDisplayTags(detail: SourceDetail | null | undefined): string[] {
  if (!detail) return [];
  if (detail.frontend_category === "content" && detail.source_platform) {
    return [detail.source_platform];
  }
  return detail.entity_tags;
}

interface Props {
  slug: string | null;
  onClose: () => void;
}

export function EntityDrawer({ slug, onClose }: Props) {
  const { isZh } = useLanguage();
  const { data: detail, isLoading } = useSourceDetail(slug);

  return (
    <>
      {slug && (
        <div
          className="fixed inset-0 bg-slate-900/10 backdrop-blur-sm z-40 dark:bg-black/45"
          onClick={onClose}
        />
      )}

      <div
        className={`fixed top-0 right-0 h-full w-full max-w-[520px] bg-white shadow-2xl z-50 flex flex-col transform transition-transform duration-300 ease-in-out dark:bg-slate-950 dark:text-slate-100 dark:shadow-black/50 ${
          slug ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {slug && (
          <>
            {/* Header */}
            <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center shrink-0 dark:border-white/10">
              <div className="flex gap-2 flex-wrap">
                {getDisplayTags(detail).map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-1 rounded text-[11px] font-bold bg-slate-100 text-slate-600 dark:bg-slate-900 dark:text-slate-300"
                  >
                    {tag}
                  </span>
                ))}
              </div>
              <button
                onClick={onClose}
                className="p-1.5 rounded-full hover:bg-slate-100 text-slate-400 transition-colors shrink-0 dark:hover:bg-white/10 dark:text-slate-500 dark:hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Body */}
            <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
              {isLoading && !detail && (
                <div className="text-slate-400 text-sm text-center py-16 dark:text-slate-500">{isZh ? "加载中..." : "Loading..."}</div>
              )}

              {detail && (
                <>
                  <div className="flex items-center text-xs text-slate-400 mb-4 font-mono dark:text-slate-500">
                    <Calendar className="w-3.5 h-3.5 mr-1.5" />
                    {detail.source_date}
                    {detail.source_platform && (
                      <>
                        <span className="mx-3 text-slate-200 dark:text-slate-700">|</span>
                        <span>{detail.source_platform}</span>
                      </>
                    )}
                    {detail.source_url && (
                      <>
                        <span className="mx-3 text-slate-200 dark:text-slate-700">|</span>
                        <a
                          href={detail.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center text-blue-500 hover:underline dark:text-amber-300"
                        >
                          {isZh ? "查看原始来源" : "View source"} <ExternalLink className="w-3 h-3 ml-1" />
                        </a>
                      </>
                    )}
                  </div>

                  <h1 className="text-xl font-bold text-slate-900 mb-6 leading-snug dark:text-slate-50">
                    {isZh ? detail.title_zh || detail.title : detail.title || detail.title_zh}
                  </h1>

                  <div className="mb-6 p-4 bg-blue-50/50 rounded-lg border-l-2 border-blue-500 text-slate-700 text-[13px] leading-relaxed dark:border-amber-400 dark:bg-amber-400/10 dark:text-slate-200">
                    {isZh ? detail.tldr_zh || detail.tldr_en : detail.tldr_en || detail.tldr_zh}
                  </div>

                  <div className="prose prose-slate prose-sm max-w-none text-[14px] leading-relaxed dark:prose-invert prose-strong:text-amber-500 dark:prose-strong:text-amber-300">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {preprocessMarkdown(detail.content)}
                    </ReactMarkdown>
                  </div>
                </>
              )}
            </div>
          </>
        )}
      </div>
    </>
  );
}
