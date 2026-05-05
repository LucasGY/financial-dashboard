import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Radio } from "lucide-react";
import { EntityDrawer } from "../../features/entity-dynamics/components/EntityDrawer";
import { EntityFeed } from "../../features/entity-dynamics/components/EntityFeed";

export function EntitiesPage() {
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-[#F7F9FB] transition-colors dark:bg-slate-950 dark:text-slate-100">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Header */}
        <header className="mb-6 overflow-hidden rounded-[32px] border border-white/70 bg-[linear-gradient(135deg,#0f172a_0%,#172554_48%,#1d4ed8_100%)] px-6 py-7 text-white shadow-panel dark:!border-slate-800 dark:bg-[linear-gradient(135deg,#020617_0%,#111827_46%,#78350f_100%)] sm:px-8">
          <div className="flex items-center justify-between">
            <div>
              <Link
                to="/"
                className="inline-flex items-center gap-1.5 text-xs text-blue-200 hover:text-white transition-colors mb-3"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                返回市场全景
              </Link>
              <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-blue-100">
                <Radio className="size-3.5" />
                Entity Dynamics
              </div>
              <h1 className="mt-4 font-display text-3xl font-semibold tracking-tight sm:text-4xl">
                深度追踪与实体动态
              </h1>
              <p className="mt-3 text-sm leading-6 text-blue-100">
                实时聚合 Second Brain wiki 内容，按实体和类目过滤。
              </p>
            </div>
          </div>
        </header>

        <EntityFeed onSelectItem={setSelectedSlug} selectedSlug={selectedSlug} />
      </div>

      <EntityDrawer slug={selectedSlug} onClose={() => setSelectedSlug(null)} />

      <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background-color: #cbd5e1; border-radius: 10px; }
      `}</style>
    </div>
  );
}
