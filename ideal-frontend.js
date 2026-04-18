import React, { useState, useMemo, useRef } from 'react';
import { Activity, TrendingUp, BarChart2, AlertCircle } from 'lucide-react';

// --- 🔧 Mock Data Generators ---
const generateTimeSeries = (length, startVal, volatility, trend = 0, interval = 'day') => {
  let val = startVal;
  const now = new Date();
  return Array.from({ length }).map((_, i) => {
    val = val * (1 + (Math.random() - 0.5) * volatility + trend);
    
    // 生成对应的时间标签
    const d = new Date(now);
    if (interval === 'day') {
      d.setDate(d.getDate() - (length - 1 - i));
    } else if (interval === 'month') {
      d.setMonth(d.getMonth() - (length - 1 - i));
    }
    
    // 格式化时间标签 (日: MM/DD, 月: YYYY/MM)
    const dateStr = interval === 'day' 
      ? `${d.getMonth() + 1}/${d.getDate()}` 
      : `${d.getFullYear()}/${(d.getMonth() + 1).toString().padStart(2, '0')}`;

    return { date: dateStr, value: parseFloat(val.toFixed(2)) };
  });
};

const mockData = {
  fgValue: 21, // Current Fear & Greed (Changed to match image's "Extreme Fear")
  fgHistory: generateTimeSeries(30, 30, 0.1, -0.01, 'day').map(d => ({ ...d, value: Math.min(100, Math.max(0, d.value)) })),
  vixHistory: generateTimeSeries(30, 18, 0.15, -0.01, 'day'),
  vvixRatioHistory: generateTimeSeries(30, 4.5, 0.08, 0, 'day'),
  breadth: {
    spx: { d20: 82, d50: 65, d200: 75 },
    ndx: { d20: 15, d50: 45, d200: 60 }
  },
  valuation: {
    spx: generateTimeSeries(120, 18, 0.05, 0.002, 'month'), // 10 years (120 months)
    ndx: generateTimeSeries(120, 25, 0.06, 0.003, 'month'),
  }
};

// --- 🎨 UI Components ---

// 1. 新版半圆仪表盘 (Fear & Greed) - 仿照图片样式
const GaugeChart = ({ value }) => {
  // 颜色配置：越恐惧越绿 -> 越贪婪越红，新增 activeText 控制高亮时的文字颜色保证对比度
  const segments = [
    { label: '极度恐惧', min: 0, max: 20, color: '#166534', activeColor: '#166534', activeText: '#ffffff' }, // 深绿
    { label: '恐惧', min: 20, max: 40, color: '#22c55e', activeColor: '#22c55e', activeText: '#ffffff' },    // 绿色
    { label: '中立', min: 40, max: 60, color: '#9ca3af', activeColor: '#fbbf24', activeText: '#1f2937' },    // 灰色 -> 黄色 (黑字)
    { label: '贪婪', min: 60, max: 80, color: '#f97316', activeColor: '#f97316', activeText: '#ffffff' },    // 橙色
    { label: '极度贪婪', min: 80, max: 100, color: '#dc2626', activeColor: '#dc2626', activeText: '#ffffff' },// 深红
  ];

  // 辅助函数：将数值映射到角度 (-90 到 90 度)
  const valueToAngle = (v) => (v / 100) * 180 - 90;

  // 辅助函数：生成扇形路径
  const describeArc = (x, y, radius, startAngle, endAngle) => {
    const start = polarToCartesian(x, y, radius, endAngle);
    const end = polarToCartesian(x, y, radius, startAngle);
    const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';
    return [
      'M', start.x, start.y,
      'A', radius, radius, 0, largeArcFlag, 0, end.x, end.y
    ].join(' ');
  };

  const polarToCartesian = (centerX, centerY, radius, angleInDegrees) => {
    const angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0;
    return {
      x: centerX + (radius * Math.cos(angleInRadians)),
      y: centerY + (radius * Math.sin(angleInRadians))
    };
  };

  const cx = 150;
  const cy = 150;
  const radius = 120;
  const strokeWidth = 45; // 增加厚度，以便将文字完全包裹在扇形内
  const innerRadius = radius - strokeWidth / 2;
  const outerRadius = radius + strokeWidth / 2;
  
  // 计算指针角度
  const pointerAngle = valueToAngle(value);
  
  // 获取当前值的颜色和标签
  const activeSegment = segments.find(s => value >= s.min && value <= s.max) || segments[0];
  const currentColor = activeSegment.activeColor;
  const currentLabel = activeSegment.label;

  return (
    <div className="relative flex flex-col items-center justify-center">
      <svg viewBox="0 0 300 180" className="w-full h-auto max-w-[320px]">
        {/* 1. 绘制扇形段 */}
        {segments.map((segment, i) => {
          const startAngle = valueToAngle(segment.min);
          const endAngle = valueToAngle(segment.max);
          // 稍微留一点间隙
          const gap = 1;
          const path = describeArc(cx, cy, radius, startAngle + gap, endAngle - gap);
          const isActive = value >= segment.min && value <= segment.max;

          return (
            <g key={i}>
              {/* 底色层 */}
              <path 
                d={path} 
                fill="none" 
                stroke="#e5e7eb" // 默认灰色背景
                strokeWidth={strokeWidth} 
                strokeLinecap="butt"
                className="dark:stroke-gray-700"
              />
              {/* 高亮层 - 只有当前所在的段才显示颜色 */}
              {isActive && (
                <path 
                  d={path} 
                  fill="none" 
                  stroke={segment.activeColor}
                  strokeWidth={strokeWidth} 
                  strokeLinecap="butt"
                  className="transition-all duration-500"
                  style={{ filter: `drop-shadow(0 0 4px ${segment.activeColor}66)` }}
                />
              )}
            </g>
          );
        })}

        {/* 3. 绘制扇形标签 (文字移入扇形内部) */}
        {segments.map((segment, i) => {
          const midAngle = valueToAngle((segment.min + segment.max) / 2);
          // 将标签位置精准定在扇形的中心半径上
          const labelPos = polarToCartesian(cx, cy, radius, midAngle);
          const isActive = value >= segment.min && value <= segment.max;

          // 智能分行：如果标签是四个字（如"极度恐惧"），则拆分为两行显示
          const words = segment.label.length === 4 
            ? [segment.label.substring(0, 2), segment.label.substring(2)] 
            : [segment.label];

          return (
            <text 
              key={i}
              x={labelPos.x} 
              y={labelPos.y} 
              textAnchor="middle" 
              dominantBaseline="middle" 
              // 文字跟随弧度旋转
              transform={`rotate(${midAngle}, ${labelPos.x}, ${labelPos.y})`}
              className={`text-[11px] font-bold uppercase transition-colors duration-500 ${!isActive ? 'fill-gray-500 dark:fill-gray-400' : ''}`}
              style={{ 
                fill: isActive ? segment.activeText : undefined,
                letterSpacing: '0.05em' 
              }}
            >
              {words.map((word, idx) => (
                <tspan 
                  x={labelPos.x} 
                  dy={words.length > 1 ? (idx === 0 ? '-0.5em' : '1.1em') : '0'} 
                  key={idx}
                >
                  {word}
                </tspan>
              ))}
            </text>
          );
        })}

        {/* 4. 绘制指针 */}
        <g transform={`rotate(${pointerAngle} ${cx} ${cy})`} className="transition-transform duration-1000 ease-out">
          {/* 指针臂 */}
          <line x1={cx} y1={cy} x2={cx} y2={cy - innerRadius + 5} stroke="#1f2937" strokeWidth="4" strokeLinecap="round" className="dark:stroke-gray-100" />
          {/* 指针头 */}
          <polygon points={`${cx-5},${cy - innerRadius + 15} ${cx+5},${cy - innerRadius + 15} ${cx},${cy - innerRadius}`} fill="#1f2937" className="dark:fill-gray-100" />
        </g>

        {/* 5. 中心圆和数值 */}
        <circle cx={cx} cy={cy} r="30" fill="white" className="dark:fill-gray-800 drop-shadow-md" />
        <text x={cx} y={cy} textAnchor="middle" dominantBaseline="central" className="text-3xl font-extrabold fill-gray-900 dark:fill-white">
          {value}
        </text>
      </svg>

      {/* 底部状态文本 */}
      <div className="mt-2 text-center">
        <span className="text-lg font-bold transition-colors duration-500" style={{ color: currentColor }}>
          {currentLabel}
        </span>
      </div>
    </div>
  );
};

// 2. 迷你折线图 (Timeline) - 新增交互性
const Sparkline = ({ data, labels, color = "#3b82f6", height = 60 }) => {
  const containerRef = useRef(null);
  const [hoverIndex, setHoverIndex] = useState(null);

  if (!data || data.length === 0) return null;
  
  const min = Math.min(...data);
  const max = Math.max(...data);
  // 增加上下边距 (10% padding)，防止线条贴边
  const padding = (max - min) * 0.1 || 1;
  const paddedMin = min - padding;
  const paddedMax = max + padding;
  const range = paddedMax - paddedMin || 1;
  
  // 计算所有点的坐标
  const points = data.map((val, i) => {
    const x = (i / (data.length - 1)) * 100;
    const y = 100 - ((val - paddedMin) / range) * 100;
    return { x, y, val };
  });

  // 生成平滑的贝塞尔曲线路径 (Smooth Cubic Bezier Curve)
  let pathD = `M ${points[0].x},${points[0].y}`;
  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1];
    const curr = points[i];
    // 使用水平中点作为控制点，保证时间序列曲线的平滑自然且不过度拉伸
    const midX = (prev.x + curr.x) / 2;
    pathD += ` C ${midX},${prev.y} ${midX},${curr.y} ${curr.x},${curr.y}`;
  }

  // 闭合区域路径，用于绘制下方的渐变面积
  const areaD = `${pathD} L 100,100 L 0,100 Z`;
  const gradientId = `gradient-${color.replace('#', '')}`;

  const handleMouseMove = (e) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    // 获取鼠标在容器内的相对 X 坐标 (0 到 1 之间)
    const xPos = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    // 映射到最接近的数据点索引
    const index = Math.round(xPos * (data.length - 1));
    setHoverIndex(index);
  };

  const handleMouseLeave = () => {
    setHoverIndex(null);
  };

  return (
    <div 
      className="flex flex-col w-full relative group cursor-crosshair" 
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onTouchMove={(e) => {
         // 增加移动端触摸追踪支持
         const touch = e.touches[0];
         const rect = containerRef.current.getBoundingClientRect();
         const xPos = Math.max(0, Math.min(1, (touch.clientX - rect.left) / rect.width));
         setHoverIndex(Math.round(xPos * (data.length - 1)));
      }}
      onTouchEnd={handleMouseLeave}
    >
      {/* SVG 容器需要 relative 定位，以作为 HTML 悬浮层的参考系 */}
      <div className="relative w-full" style={{ height: `${height}px` }}>
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full overflow-visible">
          <defs>
            <linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity="0.35" />
              <stop offset="100%" stopColor={color} stopOpacity="0.01" />
            </linearGradient>
          </defs>
          {/* 渐变面积 */}
          <path d={areaD} fill={`url(#${gradientId})`} />
          {/* 平滑折线 */}
          <path 
            d={pathD} 
            fill="none" 
            stroke={color} 
            strokeWidth="1.5" 
            strokeLinecap="round" 
            vectorEffect="non-scaling-stroke"
            style={{ filter: `drop-shadow(0px 2px 3px ${color}33)` }}
          />
          
          {/* 交互时的垂直参考线 (十字准星) */}
          {hoverIndex !== null && (
            <line 
              x1={points[hoverIndex].x} 
              y1="0" 
              x2={points[hoverIndex].x} 
              y2="100" 
              stroke="#9ca3af" 
              strokeWidth="1"
              strokeDasharray="4 4"
              vectorEffect="non-scaling-stroke"
              className="opacity-50"
            />
          )}
        </svg>

        {/* 交互时的悬浮数据点 (用 HTML 实现以保证完美的圆形，不受 SVG 拉伸影响) */}
        {hoverIndex !== null && (
          <div 
            className="absolute rounded-full border-2 border-white dark:border-gray-800 shadow-sm transition-all duration-75 z-10"
            style={{
              width: '8px',
              height: '8px',
              backgroundColor: color,
              left: `calc(${points[hoverIndex].x}% - 4px)`,
              top: `calc(${points[hoverIndex].y}% - 4px)`,
              pointerEvents: 'none'
            }}
          />
        )}

        {/* 交互式的 Tooltip 悬浮提示框 */}
        {hoverIndex !== null && (
          <div 
            className="absolute z-20 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs rounded-md py-1 px-2 shadow-lg pointer-events-none whitespace-nowrap"
            style={{
              left: `${points[hoverIndex].x}%`,
              top: `calc(${points[hoverIndex].y}% - 12px)`,
              // 智能定位：靠左靠右时改变 transform 基点，防止超出容器被边缘遮挡
              transform: points[hoverIndex].x > 85 ? 'translate(-100%, -100%)' : points[hoverIndex].x < 15 ? 'translate(0%, -100%)' : 'translate(-50%, -100%)'
            }}
          >
            <div className="font-bold text-[13px]">{points[hoverIndex].val}</div>
            <div className="text-[10px] opacity-80">{labels?.[hoverIndex]}</div>
          </div>
        )}
      </div>

      {/* 时间轴标签 (首、中、尾) */}
      {labels && labels.length > 0 && (
        <div className="flex justify-between items-center text-[10px] text-gray-400 mt-2 font-medium">
          <span>{labels[0]}</span>
          <span>{labels[Math.floor(labels.length / 2)]}</span>
          <span>{labels[labels.length - 1]}</span>
        </div>
      )}
    </div>
  );
};

// 3. 市场广度卡片
const BreadthCard = ({ title, data }) => {
  // 根据用户需求：20以下绿色，80以上红色
  const getValueColor = (val) => {
    if (val <= 20) return 'text-green-500 dark:text-green-400 font-bold';
    if (val >= 80) return 'text-red-500 dark:text-red-400 font-bold';
    return 'text-gray-700 dark:text-gray-300';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
      <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-4">{title} 成分股 &gt; 均线比例</h3>
      <div className="flex justify-between items-center">
        <div className="text-center">
          <div className="text-xs text-gray-400 mb-1">20D</div>
          <div className={`text-2xl ${getValueColor(data.d20)}`}>{data.d20}%</div>
        </div>
        <div className="w-px h-10 bg-gray-200 dark:bg-gray-700"></div>
        <div className="text-center">
          <div className="text-xs text-gray-400 mb-1">50D</div>
          <div className={`text-2xl ${getValueColor(data.d50)}`}>{data.d50}%</div>
        </div>
        <div className="w-px h-10 bg-gray-200 dark:bg-gray-700"></div>
        <div className="text-center">
          <div className="text-xs text-gray-400 mb-1">200D</div>
          <div className={`text-2xl ${getValueColor(data.d200)}`}>{data.d200}%</div>
        </div>
      </div>
    </div>
  );
};

// 4. 估值图表卡片
const ValuationCard = ({ title, dataArray }) => {
  const [period, setPeriod] = useState('10y'); // '1y', '5y', '10y'
  
  const displayData = useMemo(() => {
    const lengthMap = { '1y': 12, '5y': 60, '10y': 120 };
    return dataArray.slice(-lengthMap[period]);
  }, [dataArray, period]);

  const currentPE = displayData[displayData.length - 1].value;
  
  // 计算分位数 (当前值在历史数据中的百分位)
  const percentile = useMemo(() => {
    const sorted = [...displayData].map(d => d.value).sort((a, b) => a - b);
    const index = sorted.findIndex(v => v >= currentPE);
    return ((index / sorted.length) * 100).toFixed(1);
  }, [displayData, currentPE]);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 flex flex-col h-full">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-bold text-gray-800 dark:text-gray-100">{title}</h3>
          <p className="text-sm text-gray-500 flex items-center gap-1">
            PE (NTM) 估值 <AlertCircle size={14} />
          </p>
        </div>
        {/* 时间切换按钮 */}
        <div className="flex bg-gray-100 dark:bg-gray-900 rounded-lg p-1">
          {['1y', '5y', '10y'].map(p => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                period === p 
                  ? 'bg-white dark:bg-gray-700 shadow-sm text-blue-600 dark:text-blue-400' 
                  : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              {p.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-end gap-3 mb-6">
        <div className="text-4xl font-bold text-gray-900 dark:text-white">
          {currentPE.toFixed(1)}
        </div>
        <div className="mb-1 flex flex-col">
          <span className="text-xs text-gray-500">当前处于 {period}</span>
          <span className={`text-sm font-semibold ${percentile > 80 ? 'text-red-500' : percentile < 20 ? 'text-green-500' : 'text-gray-700 dark:text-gray-300'}`}>
            {percentile}% 分位
          </span>
        </div>
      </div>

      <div className="flex-1 mt-auto">
        <Sparkline 
          data={displayData.map(d => d.value)} 
          labels={displayData.map(d => d.date)}
          color={percentile > 80 ? '#ef4444' : '#3b82f6'} 
          height={100} 
        />
      </div>
    </div>
  );
};


// --- 🚀 Main Dashboard App ---
export default function App() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4 md:p-8 font-sans transition-colors duration-200">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header */}
        <header className="flex justify-between items-center pb-4 border-b border-gray-200 dark:border-gray-800">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <Activity className="text-blue-600" /> 市场全景终端
            </h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">实时情绪监控与核心宽基估值追踪</p>
          </div>
        </header>

        {/* --- SECTION 1: 市场情绪 --- */}
        <section>
          <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100 mb-4 flex items-center gap-2">
            <TrendingUp size={20} className="text-indigo-500" /> 1. 市场情绪 (Market Sentiment)
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* 1.1 恐贪指数 */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 flex flex-col justify-between">
              <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 text-center">CNN 恐贪指数 (Fear & Greed)</h3>
              <GaugeChart value={mockData.fgValue} />
              <div className="mt-4 border-t border-gray-100 dark:border-gray-700 pt-4">
                <div className="text-xs text-gray-400 mb-2 flex justify-between">
                  <span>历史走势 (30天)</span>
                  <span>{mockData.fgHistory[0].value.toFixed(0)} → {mockData.fgValue}</span>
                </div>
                <Sparkline 
                  data={mockData.fgHistory.map(d => d.value)} 
                  labels={mockData.fgHistory.map(d => d.date)}
                  color="#8b5cf6" 
                  height={40} 
                />
              </div>
            </div>

            {/* 1.2 VIX & VVIX */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 flex flex-col gap-4">
              <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400">波动率指标 (Volatility)</h3>
              
              <div className="flex-1 bg-gray-50 dark:bg-gray-900/50 rounded-lg p-3">
                <div className="flex justify-between items-end mb-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">VIX (恐慌指数)</span>
                  <span className="text-lg font-bold text-gray-900 dark:text-white">
                    {mockData.vixHistory[mockData.vixHistory.length-1].value}
                  </span>
                </div>
                <Sparkline 
                  data={mockData.vixHistory.map(d=>d.value)} 
                  labels={mockData.vixHistory.map(d=>d.date)}
                  color="#f59e0b" 
                  height={35} 
                />
              </div>

              <div className="flex-1 bg-gray-50 dark:bg-gray-900/50 rounded-lg p-3">
                <div className="flex justify-between items-end mb-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">VVIX / VIX (波动率结构)</span>
                  <span className="text-lg font-bold text-gray-900 dark:text-white">
                    {mockData.vvixRatioHistory[mockData.vvixRatioHistory.length-1].value}
                  </span>
                </div>
                <Sparkline 
                  data={mockData.vvixRatioHistory.map(d=>d.value)} 
                  labels={mockData.vvixRatioHistory.map(d=>d.date)}
                  color="#10b981" 
                  height={35} 
                />
              </div>
            </div>

            {/* 1.3 市场广度 */}
            <div className="flex flex-col gap-4">
              <BreadthCard title="S&P 500" data={mockData.breadth.spx} />
              <BreadthCard title="NASDAQ 100" data={mockData.breadth.ndx} />
            </div>
          </div>
        </section>

        {/* --- SECTION 2: 指数估值 --- */}
        <section>
          <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100 mb-4 flex items-center gap-2 mt-8">
            <BarChart2 size={20} className="text-blue-500" /> 2. 核心指数估值 (Index Valuation)
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-[320px]">
            <ValuationCard 
              title="S&P 500" 
              dataArray={mockData.valuation.spx} 
            />
            <ValuationCard 
              title="NASDAQ-100" 
              dataArray={mockData.valuation.ndx} 
            />
          </div>
        </section>

        <footer className="text-center text-sm text-gray-400 py-8">
          Mock Project Dashboard &copy; {new Date().getFullYear()} - Created with React & Tailwind
        </footer>
      </div>
    </div>
  );
}