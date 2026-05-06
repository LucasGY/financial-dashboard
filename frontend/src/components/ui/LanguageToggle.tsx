import { Languages } from "lucide-react";
import { useLanguage } from "../../app/language";

export function LanguageToggle() {
  const { language, setLanguage } = useLanguage();

  return (
    <div className="flex rounded-full border border-slate-200/80 bg-white/90 p-1 shadow-panel backdrop-blur dark:border-white/10 dark:bg-slate-950/82">
      <span className="inline-flex items-center px-2 text-slate-400 dark:text-slate-500">
        <Languages className="size-3.5" />
      </span>
      {[
        { value: "zh", label: "中文" },
        { value: "en", label: "En" }
      ].map((item) => {
        const isActive = language === item.value;

        return (
          <button
            key={item.value}
            type="button"
            onClick={() => setLanguage(item.value as "zh" | "en")}
            className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
              isActive
                ? "bg-slate-950 text-white shadow-sm dark:bg-amber-400 dark:text-slate-950"
                : "text-slate-500 hover:text-slate-950 dark:text-slate-400 dark:hover:text-white"
            }`}
            aria-pressed={isActive}
          >
            {item.label}
          </button>
        );
      })}
    </div>
  );
}
