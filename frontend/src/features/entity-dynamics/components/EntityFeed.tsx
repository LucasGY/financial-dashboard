import { useMemo, useState } from "react";
import { Activity, BookOpen, Calendar, FileText, Mic } from "lucide-react";
import { useLanguage } from "../../../app/language";
import { useEntityFeed } from "../hooks";
import type { ContentType, FeedItem, FrontendCategory } from "../types";

const CATEGORIES: { id: "all" | FrontendCategory; label: string; labelEn: string }[] = [
  { id: "all", label: "全部动态", labelEn: "All Updates" },
  { id: "mag7", label: "核心巨头", labelEn: "Mega Caps" },
  { id: "ai", label: "AI 独角兽", labelEn: "AI Unicorns" },
  { id: "content", label: "深度内容", labelEn: "Deep Content" },
];

const SECONDARY_TAGS: Record<FrontendCategory, string[]> = {
  mag7: ["AMZN", "MSFT", "NVDA", "AAPL", "META", "GOOGL", "TSLA", "BRK", "TSMC"],
  ai: ["OpenAI", "Anthropic"],
  content: ["YouTube", "X", "WeChat", "Web"],
};

const CONTENT_ICONS: Record<ContentType, { Icon: React.ElementType; className: string }> = {
  podcast: { Icon: Mic, className: "text-purple-500" },
  article: { Icon: FileText, className: "text-slate-500" },
  news: { Icon: Activity, className: "text-blue-500" },
  release: { Icon: FileText, className: "text-green-500" },
  tweet: { Icon: Activity, className: "text-sky-500" },
  research: { Icon: BookOpen, className: "text-orange-500" },
};

function isToday(dateStr: string): boolean {
  return dateStr.startsWith(new Date().toISOString().slice(0, 10));
}

function getContentIcon(contentType: string) {
  return CONTENT_ICONS[contentType as ContentType] ?? { Icon: FileText, className: "text-slate-500" };
}

interface Props {
  onSelectItem: (slug: string) => void;
  selectedSlug: string | null;
}

export function EntityFeed({ onSelectItem, selectedSlug }: Props) {
  const { isZh } = useLanguage();
  const { data, isLoading, error } = useEntityFeed();
  const [activeCategory, setActiveCategory] = useState<"all" | FrontendCategory>("all");
  const [activeEntity, setActiveEntity] = useState<string>("all");

  const allItems = data?.items ?? [];

  const itemsInCategory = useMemo(() => {
    if (activeCategory === "all") return allItems;
    return allItems.filter((item) => item.frontend_category === activeCategory);
  }, [allItems, activeCategory]);

  const entityOptions = useMemo(() => {
    if (activeCategory === "all") return [];
    return SECONDARY_TAGS[activeCategory];
  }, [activeCategory]);

  const availableEntityOptions = useMemo(() => {
    if (activeCategory === "all") return new Set<string>();
    return new Set(
      itemsInCategory.flatMap((item) =>
        activeCategory === "content" && item.source_platform ? [item.source_platform] : item.entity_tags
      )
    );
  }, [activeCategory, itemsInCategory]);

  const filteredItems = useMemo(() => {
    if (activeEntity === "all") return itemsInCategory;
    return itemsInCategory.filter((item) =>
      activeCategory === "content" ? item.source_platform === activeEntity : item.entity_tags.includes(activeEntity)
    );
  }, [activeCategory, itemsInCategory, activeEntity]);

  const handleCategoryClick = (id: "all" | FrontendCategory) => {
    setActiveCategory(id);
    setActiveEntity("all");
  };

  return (
    <div className="flex flex-col rounded-2xl border border-slate-100 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-[#0b1220]">
      {/* Filter area */}
      <div className="mb-6 border-b border-slate-100 pb-5 dark:border-white/10">
        <div className="flex flex-wrap gap-2 mb-3">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() => handleCategoryClick(cat.id)}
              className={`px-3.5 py-1.5 rounded-full text-[13px] font-medium transition-colors ${
                activeCategory === cat.id
                  ? "bg-slate-800 text-white shadow-sm dark:bg-amber-400 dark:text-slate-950"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-950/70 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
              }`}
            >
              {isZh ? cat.label : cat.labelEn}
            </button>
          ))}
        </div>

        {activeCategory !== "all" && entityOptions.length > 0 && (
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setActiveEntity("all")}
              className={`px-2.5 py-1 rounded text-xs font-semibold border transition-colors ${
                activeEntity === "all"
                  ? "border-slate-800 text-slate-800 bg-slate-50 dark:border-amber-400 dark:bg-amber-400/10 dark:text-amber-300"
                  : "border-slate-200 text-slate-500 hover:border-slate-400 dark:border-slate-700 dark:text-slate-400 dark:hover:border-slate-500"
              }`}
            >
              {isZh ? "全部" : "All"}
            </button>
            {entityOptions.map((entity) => (
              <button
                key={entity}
                onClick={() => {
                  if (availableEntityOptions.has(entity)) setActiveEntity(entity);
                }}
                disabled={!availableEntityOptions.has(entity)}
                className={`px-2.5 py-1 rounded text-xs font-semibold border transition-colors ${
                  activeEntity === entity
                    ? "border-blue-500 text-blue-600 bg-blue-50 dark:border-amber-400 dark:bg-amber-400/10 dark:text-amber-300"
                    : !availableEntityOptions.has(entity)
                      ? "border-slate-100 text-slate-300 bg-slate-50 cursor-not-allowed dark:border-white/5 dark:bg-slate-950/30 dark:text-slate-700"
                    : "border-slate-200 text-slate-500 hover:border-slate-400 dark:border-slate-700 dark:text-slate-400 dark:hover:border-slate-500"
                }`}
              >
                {entity}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Timeline */}
      <div className="relative">
        <div className="absolute left-[11px] top-4 bottom-0 w-[2px] bg-slate-100 dark:bg-slate-800" />

        {isLoading && (
          <div className="pl-8 py-10 text-center text-slate-400 text-sm dark:text-slate-500">{isZh ? "加载中..." : "Loading..."}</div>
        )}

        {error && (
          <div className="pl-8 py-10 text-center text-red-400 text-sm dark:text-red-300">{isZh ? "加载失败，请检查后端服务" : "Failed to load. Check the backend service."}</div>
        )}

        {!isLoading && !error && filteredItems.length === 0 && (
          <div className="pl-8 py-10 text-center text-slate-400 text-sm dark:text-slate-500">{isZh ? "没有找到相关的动态内容" : "No matching updates found"}</div>
        )}

        <div className="space-y-3 pt-1 pb-4">
          {filteredItems.map((item) => (
            <FeedCard
              key={item.slug}
              item={item}
              isSelected={item.slug === selectedSlug}
              onClick={() => onSelectItem(item.slug)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function FeedCard({
  item,
  isSelected,
  onClick,
}: {
  item: FeedItem;
  isSelected: boolean;
  onClick: () => void;
}) {
  const { isZh } = useLanguage();
  const { Icon, className: iconClassName } = getContentIcon(item.content_type);
  const today = isToday(item.source_date);

  return (
    <div className="relative pl-8 group cursor-pointer" onClick={onClick}>
      <div
        className={`absolute left-[7px] top-[18px] z-10 w-2.5 h-2.5 rounded-full ring-2 ring-white transition-transform group-hover:scale-110 dark:ring-slate-950 ${
          today ? "bg-green-500" : "bg-slate-400"
        }`}
      />

      <div
        className={`border rounded-xl p-3.5 transition-all duration-200 ${
          isSelected
            ? "bg-blue-50/60 border-blue-300 shadow-sm dark:border-amber-400/60 dark:bg-amber-400/10"
            : "bg-white border-slate-100/60 hover:shadow-sm hover:bg-slate-50/50 group-hover:border-blue-200 dark:border-slate-800 dark:bg-[#111827] dark:hover:bg-slate-800 dark:group-hover:border-slate-600"
        }`}
      >
        <div className="flex justify-between items-start mb-1.5">
          <div className="flex items-center gap-2.5">
            <span className="text-[11px] font-mono text-slate-400 flex items-center dark:text-slate-500">
              <Calendar className="w-[10px] h-[10px] mr-1" />
              {item.source_date}
            </span>
            <div className="flex gap-1">
              {(item.frontend_category === "content" && item.source_platform
                ? [item.source_platform]
                : item.entity_tags
              ).map((tag) => (
                <span
                  key={tag}
                  className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-white border border-slate-200 text-slate-500 uppercase tracking-wider dark:border-slate-700 dark:bg-slate-950 dark:text-slate-400"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
          <Icon className={`w-3.5 h-3.5 opacity-70 ${iconClassName}`} />
        </div>

        <h3
          className={`text-[14px] font-bold mb-1 transition-colors line-clamp-1 leading-snug ${
            isSelected ? "text-blue-700 dark:text-amber-300" : "text-slate-800 group-hover:text-blue-600 dark:text-slate-100 dark:group-hover:text-amber-300"
          }`}
        >
          {isZh ? item.title_zh || item.title : item.title || item.title_zh}
        </h3>
        <p className="text-[13px] text-slate-500 line-clamp-2 leading-relaxed dark:text-slate-400">
          {isZh ? item.tldr_zh || item.tldr_en : item.tldr_en || item.tldr_zh}
        </p>
      </div>
    </div>
  );
}
