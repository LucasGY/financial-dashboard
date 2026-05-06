import { useId, useRef, useState } from "react";

type SparklineProps = {
  data: Array<number | null>;
  labels?: string[];
  color?: string;
  height?: number;
};

type Point = {
  x: number;
  y: number;
  value: number;
};

const getPathD = (points: Point[]) => {
  let pathD = `M ${points[0].x},${points[0].y}`;

  for (let index = 1; index < points.length; index += 1) {
    const prev = points[index - 1];
    const current = points[index];
    const midX = (prev.x + current.x) / 2;
    pathD += ` C ${midX},${prev.y} ${midX},${current.y} ${current.x},${current.y}`;
  }

  return pathD;
};

export function Sparkline({ data, labels, color = "#2563eb", height = 72 }: SparklineProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const gradientId = useId().replace(/:/g, "");
  const filtered = data
    .map((value, index) => (value === null ? null : { value, index }))
    .filter((point): point is { value: number; index: number } => point !== null);

  if (filtered.length < 2) {
    return <div className="flex h-[72px] items-center justify-center text-xs text-slate-400">暂无趋势数据</div>;
  }

  const min = Math.min(...filtered.map((item) => item.value));
  const max = Math.max(...filtered.map((item) => item.value));
  const padding = (max - min) * 0.1 || 1;
  const range = max + padding - (min - padding) || 1;
  const points = filtered.map((item) => ({
    x: (item.index / (data.length - 1 || 1)) * 100,
    y: 100 - ((item.value - (min - padding)) / range) * 100,
    value: item.value
  }));
  const pathD = getPathD(points);
  const areaD = `${pathD} L 100,100 L 0,100 Z`;

  const setPosition = (clientX: number) => {
    if (!containerRef.current) {
      return;
    }

    const rect = containerRef.current.getBoundingClientRect();
    const relativeX = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
    let nearestIndex = 0;
    let nearestDistance = Number.POSITIVE_INFINITY;

    points.forEach((point, index) => {
      const distance = Math.abs(point.x / 100 - relativeX);
      if (distance < nearestDistance) {
        nearestIndex = index;
        nearestDistance = distance;
      }
    });

    setHoverIndex(nearestIndex);
  };

  const activePoint = hoverIndex === null ? null : points[hoverIndex];
  const activeLabel = hoverIndex === null ? undefined : labels?.[filtered[hoverIndex].index];

  return (
    <div className="flex w-full flex-col">
      <div
        ref={containerRef}
        className="relative w-full cursor-crosshair touch-pan-x"
        style={{ height }}
        onMouseMove={(event) => setPosition(event.clientX)}
        onMouseLeave={() => setHoverIndex(null)}
        onTouchMove={(event) => setPosition(event.touches[0].clientX)}
        onTouchEnd={() => setHoverIndex(null)}
      >
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="h-full w-full overflow-visible">
          <defs>
            <linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity="0.32" />
              <stop offset="100%" stopColor={color} stopOpacity="0.02" />
            </linearGradient>
          </defs>

          <path d={areaD} fill={`url(#${gradientId})`} />
          <path
            d={pathD}
            fill="none"
            stroke={color}
            strokeWidth="1.8"
            strokeLinecap="round"
            vectorEffect="non-scaling-stroke"
            style={{ filter: `drop-shadow(0px 6px 10px ${color}1f)` }}
          />

          {activePoint ? (
            <line
              x1={activePoint.x}
              y1="0"
              x2={activePoint.x}
              y2="100"
              stroke="#94a3b8"
              strokeWidth="1"
              strokeDasharray="4 5"
              vectorEffect="non-scaling-stroke"
            />
          ) : null}
        </svg>

        {activePoint ? (
          <>
            <div
              className="absolute z-10 size-2 rounded-full border-2 border-white shadow-sm"
              style={{
                left: `calc(${activePoint.x}% - 4px)`,
                top: `calc(${activePoint.y}% - 4px)`,
                backgroundColor: color
              }}
            />
            <div
              className="absolute z-20 rounded-md bg-slate-950 px-2 py-1 text-xs text-white shadow-lg"
              style={{
                left: `${activePoint.x}%`,
                top: `calc(${activePoint.y}% - 12px)`,
                transform:
                  activePoint.x > 85 ? "translate(-100%, -100%)" : activePoint.x < 15 ? "translate(0%, -100%)" : "translate(-50%, -100%)"
              }}
            >
              <div className="font-semibold">{activePoint.value.toFixed(2)}</div>
              {activeLabel ? <div className="text-[10px] text-slate-300">{activeLabel}</div> : null}
            </div>
          </>
        ) : null}
      </div>

      {labels && labels.length > 0 ? (
        <div className="mt-2 flex items-center justify-between text-[10px] font-medium text-slate-400">
          <span>{labels[0]}</span>
          <span>{labels[Math.floor(labels.length / 2)]}</span>
          <span>{labels[labels.length - 1]}</span>
        </div>
      ) : null}
    </div>
  );
}
