import { Activity, BarChart2, BrainCircuit, TrendingUp } from "lucide-react";
import { AsyncState } from "../../components/ui/AsyncState";
import { SectionTitle } from "../../components/ui/SectionTitle";
import { BreadthCard } from "../../features/sentiment/components/BreadthCard";
import { FearGreedCard } from "../../features/sentiment/components/FearGreedCard";
import { VolatilityCard } from "../../features/sentiment/components/VolatilityCard";
import { StrategyLabPanel } from "../../features/strategy-lab/components/StrategyLabPanel";
import { useSentimentData } from "../../features/sentiment/hooks";
import { ValuationCard } from "../../features/valuation/components/ValuationCard";

export function DashboardPage() {
  const { data, error, isLoading } = useSentimentData();
  const breadthCards = data
    ? [data.overview.breadth.spx, data.overview.breadth.ndx].filter((item): item is NonNullable<typeof item> => item !== null)
    : [];
  const isEmpty = !data || (!data.fearGreedTrend.series.length && !data.volatilityTrend.vix_series.length && breadthCards.length === 0);

  return (
    <main className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-8">
        <header className="overflow-hidden rounded-[32px] border border-white/70 bg-[linear-gradient(135deg,#0f172a_0%,#172554_48%,#1d4ed8_100%)] px-6 py-7 text-white shadow-panel sm:px-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-blue-100">
                <Activity className="size-3.5" />
                Financial Dashboard
              </div>
              <h1 className="mt-4 font-display text-3xl font-semibold tracking-tight sm:text-4xl">市场全景终端</h1>
              <p className="mt-3 text-sm leading-6 text-blue-100 sm:text-base">
                实时情绪监控与核心宽基估值追踪，直接消费后端统一口径接口，减少首屏判断成本。
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:max-w-sm sm:grid-cols-2">
              <div className="rounded-2xl border border-white/12 bg-white/10 px-4 py-3">
                <div className="text-xs uppercase tracking-[0.18em] text-blue-100">情绪模块</div>
                <div className="mt-2 text-lg font-semibold">Fear &amp; Greed / VIX</div>
              </div>
              <div className="rounded-2xl border border-white/12 bg-white/10 px-4 py-3">
                <div className="text-xs uppercase tracking-[0.18em] text-blue-100">估值模块</div>
                <div className="mt-2 text-lg font-semibold">SPX / NDX Timeline</div>
              </div>
            </div>
          </div>
        </header>

        <section className="space-y-5">
          <SectionTitle
            title="1. 市场情绪"
            subtitle="首屏聚合展示风险偏好、波动率结构和市场内部参与度。"
            icon={TrendingUp}
            iconClassName="text-indigo-600"
          />

          <AsyncState isLoading={isLoading} error={error} isEmpty={isEmpty} emptyLabel="市场情绪数据暂不可用">
            {data ? (
              <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1.08fr_0.92fr_0.9fr]">
                <FearGreedCard snapshot={data.overview.fear_greed} trend={data.fearGreedTrend} />
                <VolatilityCard
                  vix={data.overview.vix}
                  volStructure={data.overview.vol_structure}
                  trend={data.volatilityTrend}
                />
                <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-1">
                  {breadthCards.length > 0 ? breadthCards.map((item) => <BreadthCard key={item.index_code} snapshot={item} />) : null}
                </div>
              </div>
            ) : null}
          </AsyncState>
        </section>

        <section className="space-y-5">
          <SectionTitle
            title="2. 核心指数估值"
            subtitle="窗口切换完全以后端 timeline 结果为准，不在前端重复计算分位。"
            icon={BarChart2}
            iconClassName="text-blue-600"
          />

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
            <ValuationCard index="SPX" title="S&P 500" />
            <ValuationCard index="NDX" title="NASDAQ-100" />
          </div>
        </section>

        <section className="space-y-5">
          <SectionTitle
            title="3. Strategy Lab"
            subtitle="用自然语言描述策略，实时生成受控规则与代码，并输出未来窗口的胜率和回报统计。"
            icon={BrainCircuit}
            iconClassName="text-emerald-600"
          />

          <StrategyLabPanel />
        </section>
      </div>
    </main>
  );
}
