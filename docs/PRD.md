# Financial Dashboard PRD

## 1. 项目背景

本项目用于构建一个追踪美股市场情绪与核心指数估值的金融数据看板。目标是将已经存储在 MariaDB 中的多类指标数据，通过统一的 Web Dashboard 进行集中展示，帮助用户快速判断当前市场温度、波动风险、市场广度和估值位置。

当前已有两项基础输入：

- 前端目标样式原型：[ideal-frontend.js](/Users/lucasgou/Desktop/projects/financial-dashboard/ideal-frontend.js)
- MariaDB 真实表结构：
  - [raw_fng.sql](/Users/lucasgou/Desktop/projects/financial-dashboard/raw_fng.sql)
  - [raw_vix.sql](/Users/lucasgou/Desktop/projects/financial-dashboard/raw_vix.sql)
  - [market_breadth.sql](/Users/lucasgou/Desktop/projects/financial-dashboard/market_breadth.sql)
  - [index_valuation.sql](/Users/lucasgou/Desktop/projects/financial-dashboard/index_valuation.sql)

本期目标不是做交易系统，也不是做数据采集平台，而是做一个只读型、分析型、可快速扫描的金融数据终端。

## 2. 产品目标

### 2.1 核心目标

为用户提供一个单页 Dashboard，用于快速回答以下问题：

- 当前市场情绪处于什么位置
- 当前波动率是否处于异常状态
- 市场内部上涨广度是否健康
- 核心宽基指数当前估值处于历史什么位置

### 2.2 产品目标拆解

- 将分散的情绪和估值指标统一到同一页面中
- 保证首页首屏即可看到所有核心结论
- 将“当前值”和“历史位置”同时展示，避免只看点位不看背景
- 保持高信息密度，同时维持清晰的视觉层级

### 2.3 非目标

本期不包含以下范围：

- 用户登录、权限系统
- 自定义看板拖拽
- 多资产类别扩展
- 实时推送/WebSocket
- 下单、提醒、交易执行
- 数据抓取与清洗平台重构

## 3. 用户与使用场景

### 3.1 目标用户

- 你本人，作为主要使用者
- 小范围内部研究/分析使用者

### 3.2 核心使用场景

#### 场景 A：开盘前快速扫描

用户打开 Dashboard，希望在 10-20 秒内了解：

- 恐贪指数处于恐惧还是贪婪
- VIX 是否明显上升
- 广度是否恶化
- SPX / NDX 的估值是否处于高位分位

#### 场景 B：盘后复盘

用户查看最近 30 天情绪与波动率趋势，并结合估值分位判断市场是否进入极端区间。

#### 场景 C：中期判断

用户查看 `1Y / 5Y / 10Y` 的估值切换，判断当前市场相对历史的位置，而不是只看单一数值。

## 4. 页面信息架构

产品当前采用单页结构，页面由两个一级模块构成：

1. `Market Sentiment`
2. `Index Valuation`

整体结构参考原型中的单页纵向排列，不拆多路由，不做复杂导航。

```text
Dashboard
├── Header
├── Section 1: Market Sentiment
│   ├── Fear & Greed Card
│   ├── Volatility Card
│   └── Breadth Cards
└── Section 2: Index Valuation
    ├── S&P 500 Valuation Card
    └── NASDAQ-100 Valuation Card
```

## 5. 页面模块

### 5.1 Header

展示内容：

- 标题：`市场全景终端`
- 副标题：`实时情绪监控与核心宽基估值追踪`

要求：

- 保持简洁，不承载筛选器
- 作为页面识别性入口，不承担业务交互

### 5.2 Market Sentiment

#### 5.2.1 CNN Fear & Greed Card

展示内容：

- 当前值
- 半圆仪表盘
- 当前情绪状态标签
- 最近 30 天走势 sparkline
- 30 天区间起止值

目的：

- 提供对整体市场风险偏好的直观判断

#### 5.2.2 Volatility Card

展示内容：

- `VIX` 当前值与走势
- `VVIX / VIX / 3.5` 当前值与走势

目的：

- 判断市场是否处于波动率抬升阶段
- 用波动率结构识别恐慌是否扩散或钝化

#### 5.2.3 Breadth Cards

展示内容：

- `S&P 500` 成分股高于 `20D / 50D / 200D` 均线比例
- `NASDAQ 100` 成分股高于 `20D / 50D / 200D` 均线比例

目的：

- 判断指数上涨或下跌是否具有广泛参与度

### 5.3 Index Valuation

#### 5.3.1 S&P 500 Valuation Card

展示内容：

- 当前 `PE (NTM)` 数值
- `1Y / 5Y / 10Y` 切换按钮
- 当前分位数
- 对应时间窗的估值走势图

#### 5.3.2 NASDAQ-100 Valuation Card

展示内容与 SPX 相同。

目的：

- 用统一交互比较两个宽基指数当前估值是否偏高或偏低

## 6. 指标含义与展示规则

### 6.1 Fear & Greed Index

数据字段：

- `raw_fng.fng_value`

展示规则：

- `0-20`：Extreme Fear
- `21-40`：Fear
- `41-60`：Neutral
- `61-80`：Greed
- `81-100`：Extreme Greed

视觉规则：

- Extreme Fear：深绿
- Fear：绿
- Neutral：中性色/黄灰
- Greed：橙
- Extreme Greed：红

### 6.2 VIX

数据字段：

- `raw_vix.vix_close`

展示规则：

- 显示当前值
- 展示最近 30 个交易日 sparkline
- 不在本期定义固定阈值颜色，默认使用统一波动率色系

### 6.3 波动率结构

数据口径：

- `raw_vix.vvix_close / raw_vix.vix_close / 3.5`

展示规则：

- 显示当前值
- 展示最近 30 个交易日趋势
- 除零场景下应显示为空值或不可用状态

### 6.4 市场广度

数据字段：

- `market_breadth.above_20d_pct`
- `market_breadth.above_50d_pct`
- `market_breadth.above_200d_pct`

展示规则：

- 每个指数只显示最新交易日
- 数值展示为百分比

颜色规则：

- `<= 20`：绿色，表示超跌/极弱区
- `>= 80`：红色，表示过热/极强区
- 中间区间：中性色

### 6.5 指数估值

数据字段：

- `index_valuation.pe_ntm`

展示规则：

- 当前值显示 1 位小数或按接口输出格式显示
- 分位数基于所选时间窗内部历史样本计算
- 时间窗支持：
  - `1Y`
  - `5Y`
  - `10Y`

分位颜色规则：

- `<= 20%`：绿色
- `20%-80%`：中性色
- `>= 80%`：红色

## 7. 交互要求

### 7.1 页面级要求

- 页面为单页 Dashboard
- 首屏应完整呈现所有核心模块
- 不引入复杂弹窗和多层跳转

### 7.2 Fear & Greed Card

- 仪表盘根据当前值自动高亮对应区间
- 下方 30 天走势图支持 hover 查看数值与日期

### 7.3 Volatility Card

- 两条趋势图均支持 hover 查看数值与日期
- 两个子卡在视觉上保持对齐和统一结构

### 7.4 Breadth Cards

- 不需要复杂交互
- 重点是数值一眼可读

### 7.5 Valuation Cards

- `1Y / 5Y / 10Y` 切换为必须交互
- 切换后应同步更新：
  - 当前展示时间序列
  - 当前分位数
  - 当前窗口说明文字
- 走势图支持 hover 查看单点日期和值

## 8. 异常与空状态

### 8.1 数据缺失

若某模块无数据：

- 卡片保留
- 展示 `No data`
- 不隐藏模块，不改变页面结构

### 8.2 数据过期

若最新数据日期落后于当前日期：

- 接口需返回 `as_of_date`
- 前端展示最近更新时间或至少保留数据日期

### 8.3 计算失败

例如：

- `vvix_close` 为空
- `vix_close = 0`

处理要求：

- 该指标显示为空
- 其他模块不受影响

## 9. 验收标准

### 9.1 页面结构验收

- 页面结构与 [ideal-frontend.js](/Users/lucasgou/Desktop/projects/financial-dashboard/ideal-frontend.js) 对齐
- 必须包含两大模块：`Market Sentiment` 与 `Index Valuation`
- 首屏可完整看到所有核心卡片

### 9.2 数据验收

- Fear & Greed 使用 `raw_fng`
- VIX 与 VVIX 使用 `raw_vix`
- Breadth 使用 `market_breadth`
- 估值使用 `index_valuation`
- 不允许使用 mock 数据作为正式页面数据源

### 9.3 交互验收

- Fear & Greed 仪表盘正确映射区间颜色与标签
- 所有 sparkline 支持 hover 查看数值与日期
- 估值卡 `1Y / 5Y / 10Y` 切换可用
- 切换后分位数同步更新

### 9.4 展示验收

- 数值格式清晰
- 配色与极值表达符合原型逻辑
- 卡片布局在桌面端保持整齐
- 移动端至少可纵向阅读，不出现组件重叠

## 10. 版本边界

### V1 包含

- 单页 Dashboard
- 市场情绪模块
- 指数估值模块
- 与 MariaDB 真实数据联通
- 基础 hover 交互

### V1 不包含

- 鉴权
- 用户偏好存储
- 自定义筛选器系统
- 实时数据推送
- 导出 PDF/Excel
- 多市场扩展

