import { Search } from "lucide-react";
import { labelForEvent, type Language } from "../labels";
import type { Channel } from "../types";

const FILTERS: Record<Channel, { id: string; label: Record<Language, string> }[]> = {
  daily: [{ id: "all", label: { zh: "全部", en: "All" } }],
  ai: [
    { id: "all", label: { zh: "全部", en: "All" } },
    { id: "model_release", label: { zh: labelForEvent("model_release", "zh"), en: labelForEvent("model_release", "en") } },
    { id: "product_tool_update", label: { zh: labelForEvent("product_tool_update", "zh"), en: labelForEvent("product_tool_update", "en") } },
    { id: "industry", label: { zh: labelForEvent("industry", "zh"), en: labelForEvent("industry", "en") } },
    { id: "paper_research", label: { zh: labelForEvent("paper_research", "zh"), en: labelForEvent("paper_research", "en") } },
    { id: "tips_opinion", label: { zh: labelForEvent("tips_opinion", "zh"), en: labelForEvent("tips_opinion", "en") } },
  ],
  finance: [
    { id: "all", label: { zh: "全部", en: "All" } },
  ],
  deep_dive: [
    { id: "interview", label: { zh: labelForEvent("interview", "zh"), en: labelForEvent("interview", "en") } },
    { id: "manual_saved", label: { zh: labelForEvent("manual_saved", "zh"), en: labelForEvent("manual_saved", "en") } },
    { id: "close_reading", label: { zh: labelForEvent("close_reading", "zh"), en: labelForEvent("close_reading", "en") } },
  ],
};

const FINANCE_PRIMARY_ENTITIES = [
  { id: "all", label: "全部" },
  { id: "apple", label: "AAPL" },
  { id: "microsoft", label: "MSFT" },
  { id: "nvidia", label: "NVDA" },
  { id: "google", label: "GOOGL" },
  { id: "amazon", label: "AMZN" },
  { id: "meta", label: "META" },
  { id: "tesla", label: "TSLA" },
  { id: "berkshire", label: "BRK" },
  { id: "tsmc", label: "TSMC" },
];

const FINANCE_OTHER_ENTITIES = [
  { id: "spx", label: "SPX" },
  { id: "nasdaq", label: "NASDAQ" },
  { id: "us10y", label: "US10Y" },
  { id: "dxy", label: "DXY" },
  { id: "btc", label: "BTC" },
];

export function defaultFilterForChannel(channel: Channel) {
  return FILTERS[channel][0]?.id ?? "all";
}

export function TopFilterBar({
  channel,
  activeFilter,
  activeEntity,
  search,
  minScore,
  language,
  onFilterChange,
  onEntityChange,
  onSearchChange,
  onMinScoreChange,
}: {
  channel: Channel;
  activeFilter: string;
  activeEntity: string;
  search: string;
  minScore: number;
  language: Language;
  onFilterChange: (filter: string) => void;
  onEntityChange: (entity: string) => void;
  onSearchChange: (search: string) => void;
  onMinScoreChange: (score: number) => void;
}) {
  return (
    <div className="border-b border-slate-200 bg-[#f8fafc]/95 py-3 backdrop-blur dark:border-slate-800 dark:bg-slate-950/95">
      <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex flex-wrap gap-2">
          {channel === "finance" ? (
            <>
              {FINANCE_PRIMARY_ENTITIES.map((entity) => (
                <button
                  key={entity.id}
                  onClick={() => onEntityChange(entity.id)}
                  className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                    activeEntity === entity.id
                      ? "bg-slate-900 text-white dark:bg-amber-400 dark:text-slate-950"
                      : "bg-white text-slate-600 hover:bg-slate-100 dark:bg-slate-900 dark:text-slate-400 dark:hover:text-white"
                  }`}
                >
                  {entity.label}
                </button>
              ))}
              <select
                value={FINANCE_OTHER_ENTITIES.some((entity) => entity.id === activeEntity) ? activeEntity : "more"}
                onChange={(event) => onEntityChange(event.target.value === "more" ? "all" : event.target.value)}
                className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-600 outline-none dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
              >
                <option value="more">{language === "zh" ? "其他实体" : "More"}</option>
                {FINANCE_OTHER_ENTITIES.map((entity) => (
                  <option key={entity.id} value={entity.id}>
                    {entity.label}
                  </option>
                ))}
              </select>
            </>
          ) : (
            FILTERS[channel].map((filter) => (
              <button
                key={filter.id}
                onClick={() => onFilterChange(filter.id)}
                className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  activeFilter === filter.id
                    ? "bg-slate-900 text-white dark:bg-amber-400 dark:text-slate-950"
                    : "bg-white text-slate-600 hover:bg-slate-100 dark:bg-slate-900 dark:text-slate-400 dark:hover:text-white"
                }`}
              >
                {filter.label[language]}
              </button>
            ))
          )}
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <label className="flex min-w-0 items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900">
            <Search className="size-4 shrink-0" />
            <input
              value={search}
              onChange={(event) => onSearchChange(event.target.value)}
              placeholder={language === "zh" ? "搜索标题/摘要..." : "Search title/summary..."}
              className="min-w-0 flex-1 bg-transparent text-slate-900 outline-none placeholder:text-slate-400 dark:text-white"
            />
          </label>
          <label className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900">
            <span className="whitespace-nowrap">{language === "zh" ? "最低分" : "Min score"}</span>
            <select
              value={minScore}
              onChange={(event) => onMinScoreChange(Number(event.target.value))}
              className="bg-transparent text-slate-900 outline-none dark:text-white"
            >
              {[0, 50, 60, 70, 80, 90].map((score) => (
                <option key={score} value={score}>
                  {score === 0 ? (language === "zh" ? "不限" : "Any") : `${score}+`}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>
    </div>
  );
}
