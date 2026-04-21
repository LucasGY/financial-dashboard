import type { TimeSeriesPoint } from "../../features/sentiment/types";

type SignalMarkerPoint = {
  trade_date: string;
  price: number;
  label: string;
};

type SignalLineChartProps = {
  priceSeries: TimeSeriesPoint[];
  signalPoints: SignalMarkerPoint[];
};

type ChartPoint = {
  trade_date: string;
  x: number;
  y: number;
  value: number;
};

const buildPath = (points: ChartPoint[]) => {
  if (points.length === 0) {
    return "";
  }

  let path = `M ${points[0].x},${points[0].y}`;
  for (let index = 1; index < points.length; index += 1) {
    const previous = points[index - 1];
    const current = points[index];
    const midX = (previous.x + current.x) / 2;
    path += ` C ${midX},${previous.y} ${midX},${current.y} ${current.x},${current.y}`;
  }
  return path;
};

export function SignalLineChart({ priceSeries, signalPoints }: SignalLineChartProps) {
  const filtered = priceSeries.filter((item): item is TimeSeriesPoint & { value: number } => item.value !== null);

  if (filtered.length < 2) {
    return <div className="flex h-[180px] items-center justify-center text-xs text-slate-400">暂无价格曲线</div>;
  }

  const min = Math.min(...filtered.map((item) => item.value));
  const max = Math.max(...filtered.map((item) => item.value));
  const padding = (max - min) * 0.15 || 1;
  const range = max + padding - (min - padding) || 1;
  const points = filtered.map((item, index) => ({
    trade_date: item.trade_date,
    x: (index / Math.max(filtered.length - 1, 1)) * 100,
    y: 100 - ((item.value - (min - padding)) / range) * 100,
    value: item.value
  }));
  const pointMap = new Map(points.map((item) => [item.trade_date, item]));

  return (
    <div className="space-y-3">
      <div className="h-[180px] overflow-hidden rounded-[24px] border border-slate-200 bg-[linear-gradient(180deg,rgba(37,99,235,0.08),rgba(255,255,255,0))] p-3">
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="h-full w-full overflow-visible">
          <path d={buildPath(points)} fill="none" stroke="#2563eb" strokeWidth="1.8" vectorEffect="non-scaling-stroke" />
          {signalPoints.map((item) => {
            const point = pointMap.get(item.trade_date);
            if (!point) {
              return null;
            }

            return (
              <g key={item.label}>
                <line
                  x1={point.x}
                  y1="8"
                  x2={point.x}
                  y2="100"
                  stroke="#fb7185"
                  strokeWidth="1"
                  strokeDasharray="3 4"
                  vectorEffect="non-scaling-stroke"
                />
                <circle cx={point.x} cy={point.y} r="2.2" fill="#fb7185" />
              </g>
            );
          })}
        </svg>
      </div>
      <div className="flex items-center justify-between text-[10px] font-medium text-slate-400">
        <span>{filtered[0].trade_date}</span>
        <span>{filtered[Math.floor(filtered.length / 2)].trade_date}</span>
        <span>{filtered[filtered.length - 1].trade_date}</span>
      </div>
    </div>
  );
}
