import { AlertCircle, LoaderCircle } from "lucide-react";
import type { ReactNode } from "react";
import { useLanguage } from "../../app/language";

type AsyncStateProps = {
  isLoading: boolean;
  error: Error | null;
  isEmpty?: boolean;
  loadingLabel?: string;
  emptyLabel?: string;
  children: ReactNode;
};

export function AsyncState({
  isLoading,
  error,
  isEmpty = false,
  loadingLabel,
  emptyLabel,
  children
}: AsyncStateProps) {
  const { isZh } = useLanguage();
  const resolvedLoadingLabel = loadingLabel ?? (isZh ? "正在加载数据..." : "Loading data...");
  const resolvedEmptyLabel = emptyLabel ?? (isZh ? "暂无可展示数据" : "No data available");

  if (isLoading) {
    return (
      <div className="flex min-h-[180px] items-center justify-center rounded-[28px] border border-slate-200/70 bg-white/80 px-6 py-10 text-slate-500 shadow-panel backdrop-blur dark:border-white/10 dark:bg-slate-900/80 dark:text-slate-400">
        <div className="flex items-center gap-3 text-sm font-medium">
          <LoaderCircle className="size-4 animate-spin" />
          <span>{resolvedLoadingLabel}</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[180px] items-center justify-center rounded-[28px] border border-rose-200 bg-rose-50/90 px-6 py-10 text-center text-rose-700 shadow-panel dark:border-rose-400/30 dark:bg-rose-950/30 dark:text-rose-200">
        <div className="max-w-sm space-y-3">
          <div className="flex items-center justify-center gap-2 text-sm font-semibold">
            <AlertCircle className="size-4" />
            <span>{isZh ? "数据加载失败" : "Failed to load data"}</span>
          </div>
          <p className="text-sm leading-6">{error.message}</p>
        </div>
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className="flex min-h-[180px] items-center justify-center rounded-[28px] border border-dashed border-slate-300 bg-white/65 px-6 py-10 text-sm text-slate-500 shadow-panel dark:border-white/15 dark:bg-slate-900/60 dark:text-slate-400">
        {resolvedEmptyLabel}
      </div>
    );
  }

  return <>{children}</>;
}
