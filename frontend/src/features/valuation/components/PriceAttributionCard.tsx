import { BarChart3 } from "lucide-react";
import { useDeferredValue, useState } from "react";
import { useLanguage } from "../../../app/language";
import { AsyncState } from "../../../components/ui/AsyncState";
import { formatCompactDate } from "../../../lib/format";
import { usePriceAttribution } from "../hooks";
import type { AttributionTag } from "../types";
import { AttributionStackedBarChart } from "./AttributionStackedBarChart";

const TAGS: Array<{ value: AttributionTag; label: string; labelZh: string }> = [
  { value: "week", label: "Week", labelZh: "周" },
  { value: "month", label: "Month", labelZh: "月" }
];

const INDEXES: Array<{ value: "SPX" | "NDX"; label: string }> = [
  { value: "SPX", label: "S&P 500" },
  { value: "NDX", label: "NASDAQ-100" }
];

export function PriceAttributionCard() {
  const { isZh } = useLanguage();
  const [index, setIndex] = useState<"SPX" | "NDX">("NDX");
  const [tag, setTag] = useState<AttributionTag>("month");
  const deferredIndex = useDeferredValue(index);
  const deferredTag = useDeferredValue(tag);
  const { data, error, isLoading } = usePriceAttribution(deferredIndex, deferredTag);
  const isEmpty = !data || data.series.length === 0;

  return (
    <AsyncState isLoading={isLoading} error={error} isEmpty={isEmpty} emptyLabel={isZh ? "暂无 EPS 与估值归因数据" : "No EPS and valuation attribution data"}>
      {data ? (
        <section className="rounded-[28px] border border-slate-200/70 bg-white/88 p-5 shadow-panel backdrop-blur dark:border-white/10 dark:bg-slate-900/86 sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="flex items-center gap-2 text-sm font-semibold text-slate-500 dark:text-slate-400">
                <BarChart3 className="size-4" />
                {isZh ? "股价涨跌归因：EPS vs 估值/情绪" : "Price Move Attribution: EPS vs Valuation/Sentiment"}
              </p>
              <h3 className="mt-2 font-display text-xl font-semibold text-slate-950 dark:text-slate-50">
                {isZh ? `${data.display_name} 近一年窗口分解` : `${data.display_name} one-year window breakdown`}
              </h3>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                {isZh
                  ? `${data.ticker} 价格与 NTM PE 对齐，最新窗口结束于 ${data.as_of_date ? formatCompactDate(data.as_of_date) : "--"}`
                  : `${data.ticker} price is aligned with NTM PE. Latest window ends ${data.as_of_date ? formatCompactDate(data.as_of_date) : "--"}`}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <SegmentedControl
                items={INDEXES}
                value={index}
                onChange={(value) => setIndex(value)}
              />
              <SegmentedControl
                items={TAGS.map((item) => ({ value: item.value, label: isZh ? item.labelZh : item.label }))}
                value={tag}
                onChange={(value) => setTag(value)}
              />
            </div>
          </div>

          <div className="mt-6">
            <AttributionStackedBarChart data={data.series} />
          </div>
        </section>
      ) : null}
    </AsyncState>
  );
}

function SegmentedControl<TValue extends string>({
  items,
  value,
  onChange
}: {
  items: Array<{ value: TValue; label: string }>;
  value: TValue;
  onChange: (value: TValue) => void;
}) {
  return (
    <div className="flex rounded-full border border-slate-200 bg-slate-50 p-1 dark:border-white/10 dark:bg-slate-950/70">
      {items.map((item) => (
        <button
          key={item.value}
          type="button"
          onClick={() => onChange(item.value)}
          className={`rounded-full px-3 py-1.5 text-xs font-semibold uppercase transition ${
            value === item.value ? "bg-white text-blue-700 shadow-sm dark:bg-amber-400 dark:text-slate-950" : "text-slate-500 dark:text-slate-400"
          }`}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
