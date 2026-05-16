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
    <aside className="w-full border-b border-slate-200 bg-white px-3 py-3 dark:border-slate-800 dark:bg-slate-950 lg:fixed lg:inset-y-0 lg:left-0 lg:w-64 lg:border-b-0 lg:border-r">
      <div className="mb-5 hidden px-2 lg:block">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Workspace</div>
        <div className="mt-1 text-lg font-bold tracking-tight text-slate-950 dark:text-white">Intelligence Hub</div>
      </div>
      <nav className="flex gap-2 overflow-x-auto lg:flex-col lg:overflow-visible">
        {NAV_ITEMS.map(({ id, label, Icon }) => (
          <button
            key={id}
            onClick={() => onChange(id)}
            className={`flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition-colors ${
              activeChannel === id
                ? "bg-slate-900 text-white dark:bg-amber-400 dark:text-slate-950"
                : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-white"
            }`}
          >
            <Icon className="size-4" />
            {label}
          </button>
        ))}
      </nav>
    </aside>
  );
}
