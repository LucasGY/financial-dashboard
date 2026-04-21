type BarOverviewChartProps = {
  bars: Array<{
    label: string;
    value: number | null;
  }>;
  formatValue?: (value: number | null) => string;
  positiveColor?: string;
  negativeColor?: string;
};

export function BarOverviewChart({
  bars,
  formatValue = (value) => (value === null ? "--" : value.toFixed(1)),
  positiveColor = "#2563eb",
  negativeColor = "#ef4444"
}: BarOverviewChartProps) {
  const availableValues = bars.map((item) => item.value).filter((value): value is number => value !== null);
  const scale = Math.max(...availableValues.map((value) => Math.abs(value)), 1);

  if (availableValues.length === 0) {
    return <div className="flex h-[150px] items-center justify-center text-xs text-slate-400">暂无统计结果</div>;
  }

  return (
    <div className="space-y-3">
      {bars.map((bar) => {
        const value = bar.value;
        const width = value === null ? 0 : Math.max((Math.abs(value) / scale) * 100, 2);
        const color = (value ?? 0) >= 0 ? positiveColor : negativeColor;

        return (
          <div key={bar.label} className="space-y-1.5">
            <div className="flex items-center justify-between text-xs font-medium text-slate-500">
              <span>{bar.label}</span>
              <span className="metric-number">{formatValue(value)}</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full rounded-full transition-[width]" style={{ width: `${width}%`, backgroundColor: color }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
