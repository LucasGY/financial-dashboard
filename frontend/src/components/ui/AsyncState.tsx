import { AlertCircle, LoaderCircle } from "lucide-react";
import type { ReactNode } from "react";

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
  loadingLabel = "正在加载数据...",
  emptyLabel = "暂无可展示数据",
  children
}: AsyncStateProps) {
  if (isLoading) {
    return (
      <div className="flex min-h-[180px] items-center justify-center rounded-[28px] border border-slate-200/70 bg-white/80 px-6 py-10 text-slate-500 shadow-panel backdrop-blur">
        <div className="flex items-center gap-3 text-sm font-medium">
          <LoaderCircle className="size-4 animate-spin" />
          <span>{loadingLabel}</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[180px] items-center justify-center rounded-[28px] border border-rose-200 bg-rose-50/90 px-6 py-10 text-center text-rose-700 shadow-panel">
        <div className="max-w-sm space-y-3">
          <div className="flex items-center justify-center gap-2 text-sm font-semibold">
            <AlertCircle className="size-4" />
            <span>数据加载失败</span>
          </div>
          <p className="text-sm leading-6">{error.message}</p>
        </div>
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className="flex min-h-[180px] items-center justify-center rounded-[28px] border border-dashed border-slate-300 bg-white/65 px-6 py-10 text-sm text-slate-500 shadow-panel">
        {emptyLabel}
      </div>
    );
  }

  return <>{children}</>;
}
