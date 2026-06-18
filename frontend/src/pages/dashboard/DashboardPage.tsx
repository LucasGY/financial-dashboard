import { Activity, ArrowUpRight, BarChart2, BrainCircuit, Calculator, LineChart, Radio, TrendingUp } from "lucide-react";
import { Link } from "react-router-dom";
import { useLanguage } from "../../app/language";
import { AsyncState } from "../../components/ui/AsyncState";
import { SectionTitle } from "../../components/ui/SectionTitle";
import { BreadthCard } from "../../features/sentiment/components/BreadthCard";
import { FearGreedCard } from "../../features/sentiment/components/FearGreedCard";
import { VolatilityCard } from "../../features/sentiment/components/VolatilityCard";
import { StrategyLabPanel } from "../../features/strategy-lab/components/StrategyLabPanel";
import { useSentimentData } from "../../features/sentiment/hooks";
import { RegimeStatsPanel } from "../../features/market-regime/components/RegimeStatsPanel";
import { ValuationCard } from "../../features/valuation/components/ValuationCard";
import { PriceAttributionCard } from "../../features/valuation/components/PriceAttributionCard";
import { DrawdownScenarioCard } from "../../features/valuation/components/DrawdownScenarioCard";

const DASHBOARD_NAV_ITEMS = [
  {
    id: "overview",
    Icon: Activity,
    label: { zh: "总览", en: "Overview" },
    description: { zh: "市场全景终端", en: "Market terminal" },
  },
  {
    id: "market-sentiment",
    Icon: TrendingUp,
    label: { zh: "市场情绪", en: "Market Sentiment" },
    description: { zh: "恐贪 / VIX / 宽度", en: "Fear & Greed / VIX / Breadth" },
  },
  {
    id: "valuation",
    Icon: BarChart2,
    label: { zh: "核心估值", en: "Valuation" },
    description: { zh: "SPX / NDX / 归因", en: "SPX / NDX / Attribution" },
  },
  {
    id: "drawdown-levels",
    Icon: Calculator,
    label: { zh: "回撤点位", en: "Drawdown Levels" },
    description: { zh: "SPY / QQQ 档位", en: "SPY / QQQ levels" },
  },
  {
    id: "regime-backtest",
    Icon: LineChart,
    label: { zh: "状态回测", en: "Regime Backtest" },
    description: { zh: "历史近邻表现", en: "Historical analogs" },
  },
  {
    id: "strategy-lab",
    Icon: BrainCircuit,
    label: { zh: "策略实验室", en: "Strategy Lab" },
    description: { zh: "自然语言策略", en: "Natural language strategy" },
  },
] as const;

export function DashboardPage() {
  const { isZh } = useLanguage();
  const { data, error, isLoading } = useSentimentData();
  const breadthCards = data
    ? [data.overview.breadth.spx, data.overview.breadth.ndx].filter((item): item is NonNullable<typeof item> => item !== null)
    : [];
  const isEmpty = !data || (!data.fearGreedTrend.series.length && !data.volatilityTrend.vix_series.length && breadthCards.length === 0);

  const scrollToSection = (sectionId: string) => {
    document.getElementById(sectionId)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <main className="min-h-screen transition-colors dark:bg-slate-950 dark:text-slate-100">
      <div className="lg:pl-[208px] xl:pl-[220px]">
        <DashboardSideNav isZh={isZh} onNavigate={scrollToSection} />

        <div className="min-w-0 space-y-8 px-4 py-6 sm:px-6 lg:px-8">
          <header id="overview" className="scroll-mt-24 border-b border-slate-200 pb-4 dark:border-slate-800">
            <h1 className="font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-3xl">
              {isZh ? "市场全景终端" : "Market Overview Terminal"}
            </h1>
          </header>

        <section id="market-sentiment" className="scroll-mt-24 space-y-5">
          <SectionTitle
            title={isZh ? "1. 市场情绪" : "1. Market Sentiment"}
            subtitle={isZh ? "首屏聚合展示风险偏好、波动率结构和市场内部参与度。" : "A first-screen view of risk appetite, volatility structure, and market participation."}
            icon={TrendingUp}
            iconClassName="text-indigo-600"
          />

          <AsyncState isLoading={isLoading} error={error} isEmpty={isEmpty} emptyLabel={isZh ? "市场情绪数据暂不可用" : "Market sentiment data is unavailable"}>
            {data ? (
              <div className="grid grid-cols-1 gap-5 lg:grid-cols-2 2xl:grid-cols-4">
                <FearGreedCard snapshot={data.overview.fear_greed} trend={data.fearGreedTrend} />
                <VolatilityCard
                  vix={data.overview.vix}
                  volStructure={data.overview.vol_structure}
                  trend={data.volatilityTrend}
                />
                {breadthCards.length > 0
                  ? breadthCards.map((item) => (
                      <BreadthCard
                        key={item.index_code}
                        snapshot={item}
                        trend={item.index_code === "SPX" ? data.breadthTrend.spx : data.breadthTrend.ndx}
                      />
                    ))
                  : null}
              </div>
            ) : null}
          </AsyncState>
        </section>

        <section id="valuation" className="scroll-mt-24 space-y-5">
          <SectionTitle
            title={isZh ? "2. 核心指数估值" : "2. Core Index Valuation"}
            subtitle={isZh ? "窗口切换完全以后端 timeline 结果为准，不在前端重复计算分位。" : "Window switches use backend timeline results directly, with no duplicate percentile calculation in the frontend."}
            icon={BarChart2}
            iconClassName="text-blue-600"
          />

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
            <ValuationCard index="SPX" title="S&P 500" />
            <ValuationCard index="NDX" title="NASDAQ-100" />
          </div>
          <PriceAttributionCard />
        </section>

        <section id="drawdown-levels" className="scroll-mt-24 space-y-5">
          <SectionTitle
            title={isZh ? "3. 回撤点位计算" : "3. Drawdown Level Calculator"}
            subtitle={
              isZh
                ? "按 SPY / QQQ 距离历史高点的回撤档位，测算对应点位、隐含 PE 与历史估值分位。"
                : "Maps SPY / QQQ drawdown levels from historical highs to price levels, implied PE, and valuation percentiles."
            }
            icon={Calculator}
            iconClassName="text-amber-600"
          />

          <DrawdownScenarioCard />
        </section>

        <section id="regime-backtest" className="scroll-mt-24 space-y-5">
          <SectionTitle
            title={isZh ? "4. 当前状态回测" : "4. Current Regime Backtest"}
            subtitle={
              isZh
                ? "按最新收盘日的恐贪、VIX、50D 市场宽度和 NTM PE 分位向量寻找历史近邻，统计收盘买入后的远期表现。"
                : "Finds historical neighbors by Fear & Greed, VIX, 50D breadth, and NTM PE percentile, then measures forward returns after close."
            }
            icon={LineChart}
            iconClassName="text-cyan-600"
          />

          <RegimeStatsPanel />
        </section>

        <section id="strategy-lab" className="scroll-mt-24 space-y-5">
          <SectionTitle
            title="5. Strategy Lab"
            subtitle={
              isZh
                ? "用自然语言描述策略，实时生成受控规则与代码，并输出未来窗口的胜率和回报统计。"
                : "Describe a strategy in natural language, generate controlled rules and code, then review win-rate and return statistics."
            }
            icon={BrainCircuit}
            iconClassName="text-emerald-600"
          />

          <StrategyLabPanel />
        </section>
        </div>
      </div>
    </main>
  );
}

function DashboardSideNav({ isZh, onNavigate }: { isZh: boolean; onNavigate: (sectionId: string) => void }) {
  return (
    <aside className="border-b border-slate-200 bg-white/90 backdrop-blur dark:border-slate-800 dark:bg-slate-950/95 lg:fixed lg:inset-y-0 lg:left-0 lg:z-20 lg:w-[208px] lg:border-b-0 lg:border-r xl:w-[220px]">
      <nav className="scrollbar-none overflow-x-auto px-4 py-3 lg:overflow-visible lg:px-4 lg:py-6">
        <div className="mb-3 hidden px-1 lg:block">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{isZh ? "工作区导航" : "Workspace"}</div>
        </div>
        <div className="flex gap-1.5 lg:flex-col lg:gap-2">
          {DASHBOARD_NAV_ITEMS.map(({ id, Icon, label, description }) => (
            <button
              key={id}
              type="button"
              onClick={() => onNavigate(id)}
              className="flex min-w-[142px] shrink-0 items-center gap-2 rounded-lg px-2 py-1.5 text-left transition-colors hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/40 dark:hover:bg-slate-900 lg:min-w-0"
            >
              <span className="grid size-7 shrink-0 place-items-center rounded-md bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                <Icon className="size-3.5" />
              </span>
              <span className="min-w-0">
                <span className="block text-xs font-bold leading-4 text-slate-900 dark:text-slate-100">{isZh ? label.zh : label.en}</span>
                <span className="block truncate text-[10px] leading-4 text-slate-500 dark:text-slate-400">{isZh ? description.zh : description.en}</span>
              </span>
            </button>
          ))}
          <Link
            to="/entities"
            className="flex min-w-[152px] shrink-0 items-center gap-2 rounded-lg px-2 py-1.5 text-left transition-colors hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/40 dark:hover:bg-slate-900 lg:mt-2 lg:min-w-0 lg:border-t lg:border-slate-200 lg:pt-3 dark:lg:border-slate-800"
          >
            <span className="grid size-7 shrink-0 place-items-center rounded-md bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
              <Radio className="size-3.5" />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-xs font-bold leading-4 text-slate-900 dark:text-slate-100">{isZh ? "情报中心" : "Intelligence Hub"}</span>
              <span className="block truncate text-[10px] leading-4 text-slate-500 dark:text-slate-400">{isZh ? "打开 Hub" : "Open Hub"}</span>
            </span>
            <ArrowUpRight className="size-3 shrink-0 text-slate-400" />
          </Link>
        </div>
      </nav>
    </aside>
  );
}
