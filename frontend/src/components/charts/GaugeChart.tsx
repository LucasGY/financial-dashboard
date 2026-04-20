type GaugeChartProps = {
  value: number | null;
};

const SEGMENTS = [
  { label: "极度恐惧", min: 0, max: 20, color: "#166534", text: "#ffffff" },
  { label: "恐惧", min: 20, max: 40, color: "#22c55e", text: "#ffffff" },
  { label: "中立", min: 40, max: 60, color: "#fbbf24", text: "#111827" },
  { label: "贪婪", min: 60, max: 80, color: "#f97316", text: "#ffffff" },
  { label: "极度贪婪", min: 80, max: 100, color: "#dc2626", text: "#ffffff" }
];

const FALLBACK_VALUE = 0;

function polarToCartesian(centerX: number, centerY: number, radius: number, angleInDegrees: number) {
  const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0;

  return {
    x: centerX + radius * Math.cos(angleInRadians),
    y: centerY + radius * Math.sin(angleInRadians)
  };
}

function describeArc(x: number, y: number, radius: number, startAngle: number, endAngle: number) {
  const start = polarToCartesian(x, y, radius, endAngle);
  const end = polarToCartesian(x, y, radius, startAngle);
  const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
  return ["M", start.x, start.y, "A", radius, radius, 0, largeArcFlag, 0, end.x, end.y].join(" ");
}

const valueToAngle = (value: number) => (value / 100) * 180 - 90;

export function GaugeChart({ value }: GaugeChartProps) {
  const normalizedValue = Math.max(0, Math.min(100, value ?? FALLBACK_VALUE));
  const activeSegment = SEGMENTS.find((segment) => normalizedValue >= segment.min && normalizedValue <= segment.max) ?? SEGMENTS[0];
  const pointerAngle = valueToAngle(normalizedValue);
  const cx = 150;
  const cy = 150;
  const radius = 120;
  const strokeWidth = 44;
  const innerRadius = radius - strokeWidth / 2;
  const hubRadius = 30;
  const hubCenterY = cy;
  const pointerTipRadius = innerRadius + 2;
  const pointerBaseRadius = hubRadius - 2;
  const pointerHeadBaseRadius = innerRadius - 16;
  const pointerBaseCenter = polarToCartesian(cx, hubCenterY, pointerBaseRadius, pointerAngle);
  const pointerHeadBaseCenter = polarToCartesian(cx, hubCenterY, pointerHeadBaseRadius, pointerAngle);
  const pointerTip = polarToCartesian(cx, hubCenterY, pointerTipRadius, pointerAngle);
  const pointerHeadLeft = polarToCartesian(pointerHeadBaseCenter.x, pointerHeadBaseCenter.y, 6, pointerAngle - 90);
  const pointerHeadRight = polarToCartesian(pointerHeadBaseCenter.x, pointerHeadBaseCenter.y, 6, pointerAngle + 90);

  return (
    <div className="flex flex-col items-center justify-center">
      <svg viewBox="0 0 300 180" className="h-auto w-full max-w-[320px]">
        {SEGMENTS.map((segment) => {
          const startAngle = valueToAngle(segment.min);
          const endAngle = valueToAngle(segment.max);
          const path = describeArc(cx, cy, radius, startAngle + 1, endAngle - 1);
          const isActive = normalizedValue >= segment.min && normalizedValue <= segment.max;

          return (
            <g key={segment.label}>
              <path d={path} fill="none" stroke="#e5e7eb" strokeWidth={strokeWidth} />
              {isActive ? (
                <path
                  d={path}
                  fill="none"
                  stroke={segment.color}
                  strokeWidth={strokeWidth}
                  style={{ filter: `drop-shadow(0 0 6px ${segment.color}55)` }}
                />
              ) : null}
            </g>
          );
        })}

        {SEGMENTS.map((segment) => {
          const midAngle = valueToAngle((segment.min + segment.max) / 2);
          const labelPosition = polarToCartesian(cx, cy, radius, midAngle);
          const isActive = normalizedValue >= segment.min && normalizedValue <= segment.max;
          const words = segment.label.length === 4 ? [segment.label.slice(0, 2), segment.label.slice(2)] : [segment.label];

          return (
            <text
              key={`${segment.label}-label`}
              x={labelPosition.x}
              y={labelPosition.y}
              textAnchor="middle"
              dominantBaseline="middle"
              transform={`rotate(${midAngle}, ${labelPosition.x}, ${labelPosition.y})`}
              className="text-[11px] font-bold"
              style={{ fill: isActive ? segment.text : "#64748b", letterSpacing: "0.04em" }}
            >
              {words.map((word, index) => (
                <tspan key={word} x={labelPosition.x} dy={words.length > 1 ? (index === 0 ? "-0.55em" : "1.15em") : "0"}>
                  {word}
                </tspan>
              ))}
            </text>
          );
        })}

        <g style={{ filter: "drop-shadow(0px 1px 2px rgba(15, 23, 42, 0.18))" }}>
          <line
            x1={pointerBaseCenter.x}
            y1={pointerBaseCenter.y}
            x2={pointerHeadBaseCenter.x}
            y2={pointerHeadBaseCenter.y}
            stroke="#1f2937"
            strokeWidth="4"
            strokeLinecap="round"
          />
          <polygon points={`${pointerHeadLeft.x},${pointerHeadLeft.y} ${pointerHeadRight.x},${pointerHeadRight.y} ${pointerTip.x},${pointerTip.y}`} fill="#1f2937" />
        </g>

        <circle cx={cx} cy={hubCenterY} r={hubRadius} fill="white" style={{ filter: "drop-shadow(0px 4px 12px rgba(15, 23, 42, 0.12))" }} />
        <circle cx={cx} cy={hubCenterY} r={hubRadius - 0.75} fill="none" stroke="#e5e7eb" strokeWidth="1.5" />
        <text x={cx} y={hubCenterY} textAnchor="middle" dominantBaseline="central" className="metric-number fill-slate-950 text-3xl font-extrabold">
          {value ?? "--"}
        </text>
      </svg>

      <div className="mt-2 text-center">
        <span className="text-lg font-bold" style={{ color: activeSegment.color }}>
          {activeSegment.label}
        </span>
      </div>
    </div>
  );
}
