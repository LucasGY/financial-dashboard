import { BookOpen, BrainCircuit, ChartCandlestick, Newspaper } from "lucide-react";
import type { Channel } from "../types";

const NAV_ITEMS: { id: Channel; label: string; Icon: React.ElementType }[] = [
  { id: "daily", label: "Daily Digest", Icon: Newspaper },
  { id: "ai", label: "AI in One", Icon: BrainCircuit },
  { id: "finance", label: "Finance in One", Icon: ChartCandlestick },
  { id: "deep_dive", label: "Deep Dive", Icon: BookOpen },
];

export function IntelligenceSidebar({
  activeChannel,
  onChange,
}: {
  activeChannel: Channel;
  onChange: (channel: Channel) => void;
}) {
  return (
    <aside className="w-full border-b border-slate-200 bg-white/90 backdrop-blur dark:border-slate-800 dark:bg-slate-950/95 lg:fixed lg:inset-y-0 lg:left-0 lg:z-20 lg:w-[208px] lg:border-b-0 lg:border-r xl:w-[220px]">
      <nav className="scrollbar-none flex gap-1.5 overflow-x-auto px-4 py-3 lg:flex-col lg:gap-2 lg:overflow-visible lg:px-4 lg:py-6">
        <div className="mb-3 hidden px-1 lg:block">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Workspace</div>
        </div>
        {NAV_ITEMS.map(({ id, label, Icon }) => (
          <button
            key={id}
            onClick={() => onChange(id)}
            className={`flex min-w-[142px] shrink-0 items-center gap-2 rounded-lg px-2 py-1.5 text-left text-slate-600 transition-colors hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/40 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-white lg:min-w-0 ${
              activeChannel === id ? "ring-2 ring-blue-500/40" : ""
            }`}
          >
            <span className="grid size-7 shrink-0 place-items-center rounded-md bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
              <Icon className="size-3.5" />
            </span>
            <span className="truncate text-xs font-bold leading-4">{label}</span>
          </button>
        ))}
      </nav>
    </aside>
  );
}
