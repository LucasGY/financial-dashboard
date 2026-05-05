import { Moon, Sun } from "lucide-react";
import { useTheme } from "../../app/theme";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="fixed right-4 top-4 z-[60] flex rounded-full border border-slate-200/80 bg-white/90 p-1 shadow-panel backdrop-blur dark:border-white/10 dark:bg-slate-950/82">
      {(["dark", "light"] as const).map((item) => {
        const isActive = theme === item;
        const Icon = item === "dark" ? Moon : Sun;

        return (
          <button
            key={item}
            type="button"
            onClick={() => setTheme(item)}
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.12em] transition ${
              isActive
                ? "bg-slate-950 text-white shadow-sm dark:bg-amber-400 dark:text-slate-950"
                : "text-slate-500 hover:text-slate-950 dark:text-slate-400 dark:hover:text-white"
            }`}
            aria-pressed={isActive}
          >
            <Icon className="size-3.5" />
            {item}
          </button>
        );
      })}
    </div>
  );
}
