import type { LucideIcon } from "lucide-react";

type SectionTitleProps = {
  title: string;
  subtitle: string;
  icon: LucideIcon;
  iconClassName: string;
};

export function SectionTitle({ title, subtitle, icon: Icon, iconClassName }: SectionTitleProps) {
  return (
    <div className="flex items-start gap-4">
      <div className={`mt-1 rounded-2xl border border-white/70 bg-white/80 p-3 shadow-panel dark:border-white/10 dark:bg-slate-900/80 ${iconClassName}`}>
        <Icon className="size-5" />
      </div>
      <div className="space-y-1">
        <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-slate-50">{title}</h2>
        <p className="max-w-2xl text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>
      </div>
    </div>
  );
}
