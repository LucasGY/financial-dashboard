import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { EntityDrawer } from "../../features/entity-dynamics/components/EntityDrawer";
import { EntityFeed } from "../../features/entity-dynamics/components/EntityFeed";
import { IntelligenceSidebar } from "../../features/entity-dynamics/components/IntelligenceSidebar";
import { TopFilterBar, defaultFilterForChannel } from "../../features/entity-dynamics/components/TopFilterBar";
import { useLanguage } from "../../app/language";
import type { Language } from "../../features/entity-dynamics/labels";
import type { Channel } from "../../features/entity-dynamics/types";

const CHANNEL_COPY: Record<Channel, { title: string; description: Record<Language, string> }> = {
  daily: {
    title: "Daily Digest",
    description: { zh: "跨 AI、金融与手动沉淀的每日重点摘要。", en: "Daily highlights across AI, finance, and saved research." },
  },
  ai: {
    title: "AI in One",
    description: {
      zh: "聚合模型、产品、行业、论文与观点信号，按去重事件展示全部来源。",
      en: "A deduplicated event feed for models, products, industry moves, papers, and opinions.",
    },
  },
  finance: {
    title: "Finance in One",
    description: {
      zh: "聚合 KOL、宏观、市场、公司与行业动态，保留每个事件背后的来源链路。",
      en: "A market intelligence feed for KOL views, macro, markets, companies, and industries.",
    },
  },
  deep_dive: {
    title: "Deep Dive",
    description: {
      zh: "读取 second-brain / Obsidian 中的访谈、手动收藏与精读笔记。",
      en: "Interviews, manual saves, and close-reading notes from the second-brain vault.",
    },
  },
};

export function EntitiesPage() {
  const [activeChannel, setActiveChannel] = useState<Channel>("ai");
  const [activeFilter, setActiveFilter] = useState(defaultFilterForChannel("ai"));
  const [activeEntity, setActiveEntity] = useState("all");
  const [search, setSearch] = useState("");
  const [minScore, setMinScore] = useState(60);
  const { language } = useLanguage();
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  const channelCopy = useMemo(() => CHANNEL_COPY[activeChannel], [activeChannel]);

  useEffect(() => {
    setActiveFilter(defaultFilterForChannel(activeChannel));
    setActiveEntity("all");
    setSearch("");
    setSelectedSlug(null);
  }, [activeChannel]);

  return (
    <div className="min-h-screen bg-[#f8fafc] transition-colors dark:bg-slate-950 dark:text-slate-100">
      <IntelligenceSidebar activeChannel={activeChannel} onChange={setActiveChannel} />

      <main className="lg:pl-64">
        <div className="mx-auto max-w-6xl px-4 py-5 sm:px-6 lg:px-8">
          <div className="mb-5 border-b border-slate-200 pb-5 dark:border-slate-800">
            <div>
              <Link to="/" className="mb-3 inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
                <ArrowLeft className="size-3.5" />
                {language === "zh" ? "返回市场全景" : "Back to dashboard"}
              </Link>
              <h1 className="text-3xl font-bold tracking-tight text-slate-950 dark:text-white">{channelCopy.title}</h1>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">{channelCopy.description[language]}</p>
            </div>
          </div>

          <TopFilterBar
            channel={activeChannel}
            activeFilter={activeFilter}
            activeEntity={activeEntity}
            search={search}
            minScore={minScore}
            language={language}
            onFilterChange={setActiveFilter}
            onEntityChange={setActiveEntity}
            onSearchChange={setSearch}
            onMinScoreChange={setMinScore}
          />

          <EntityFeed
            channel={activeChannel}
            filter={activeFilter}
            entity={activeEntity}
            search={search}
            minScore={minScore}
            language={language}
            onSelectItem={setSelectedSlug}
            selectedSlug={selectedSlug}
          />
        </div>
      </main>

      <EntityDrawer slug={selectedSlug} language={language} onClose={() => setSelectedSlug(null)} />

      <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background-color: #cbd5e1; border-radius: 10px; }
      `}</style>
    </div>
  );
}
