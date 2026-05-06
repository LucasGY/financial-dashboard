import { Activity, BarChart2, BrainCircuit, LineChart, Radio, TrendingUp } from "lucide-react";
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

export function DashboardPage() {
  const { isZh } = useLanguage();
  const { data, error, isLoading } = useSentimentData();
  const breadthCards = data
    ? [data.overview.breadth.spx, data.overview.breadth.ndx].filter((item): item is NonNullable<typeof item> => item !== null)
    : [];
  const isEmpty = !data || (!data.fearGreedTrend.series.length && !data.volatilityTrend.vix_series.length && breadthCards.length === 0);

  return (
    <main className="min-h-screen px-4 py-6 transition-colors dark:bg-slate-950 dark:text-slate-100 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-8">
        <header className="overflow-hidden rounded-[32px] border border-white/70 bg-[linear-gradient(135deg,#0f172a_0%,#172554_48%,#1d4ed8_100%)] px-6 py-7 text-white shadow-panel dark:!border-slate-800 dark:bg-[linear-gradient(135deg,#020617_0%,#111827_46%,#78350f_100%)] sm:px-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-blue-100">
                <Activity className="size-3.5" />
                {isZh ? "金融仪表盘" : "Financial Dashboard"}
              </div>
              <h1 className="mt-4 font-display text-3xl font-semibold tracking-tight sm:text-4xl">
                {isZh ? "市场全景终端" : "Market Overview Terminal"}
              </h1>
              <p className="mt-3 text-sm leading-6 text-blue-100 sm:text-base">
                {isZh
                  ? "实时情绪监控与核心宽基估值追踪，直接消费后端统一口径接口，减少首屏判断成本。"
                  : "Real-time sentiment monitoring and core index valuation tracking, powered by unified backend APIs for faster first-screen decisions."}
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:max-w-sm lg:max-w-none lg:grid-cols-3">
              <div className="rounded-2xl border border-white/12 bg-white/10 px-4 py-3">
                <div className="text-xs uppercase tracking-[0.18em] text-blue-100">{isZh ? "情绪模块" : "Sentiment"}</div>
                <div className="mt-2 text-lg font-semibold">Fear &amp; Greed / VIX</div>
              </div>
              <div className="rounded-2xl border border-white/12 bg-white/10 px-4 py-3">
                <div className="text-xs uppercase tracking-[0.18em] text-blue-100">{isZh ? "估值模块" : "Valuation"}</div>
                <div className="mt-2 text-lg font-semibold">SPX / NDX Timeline</div>
              </div>
              <Link
                to="/entities"
                className="col-span-2 lg:col-span-1 rounded-2xl border border-white/12 bg-white/10 px-4 py-3 hover:bg-white/20 transition-colors"
              >
                <div className="flex items-center gap-1.5 text-xs uppercase tracking-[0.18em] text-blue-100">
                  <Radio className="size-3" />
                  {isZh ? "实体追踪" : "Entity Tracking"}
                </div>
                <div className="mt-2 text-lg font-semibold">{isZh ? "实体动态 ->" : "Entity Dynamics ->"}</div>
              </Link>
            </div>
          </div>
        </header>

        <section className="space-y-5">
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

        <section className="space-y-5">
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

        <section className="space-y-5">
          <SectionTitle
            title={isZh ? "3. 当前状态回测" : "3. Current Regime Backtest"}
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

        <section className="space-y-5">
          <SectionTitle
            title="4. Strategy Lab"
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
    </main>
  );
}
