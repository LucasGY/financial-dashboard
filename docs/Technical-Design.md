# Financial Dashboard Technical Design

## 1. 目标

本文定义 Financial Dashboard 的实现方案，重点回答以下问题：

- 前后端结构如何设计
- MariaDB 真实表如何映射到应用层
- API 如何为前端原型提供稳定数据
- 状态管理与查询口径如何统一

当前技术约束：

- 前端：`React + TailwindCSS`
- 后端：`Python FastAPI`
- 数据库：`MariaDB`
- 数据源直接读取现有真实表，不引入 SQLite

## 2. 系统架构

整体架构采用标准三层：

```text
React Frontend
    ↓ HTTP JSON
FastAPI Backend
    ↓ SQL
MariaDB
```

职责划分：

- 前端负责页面展示、交互、局部状态
- FastAPI 负责数据聚合、字段标准化、派生指标计算
- MariaDB 负责存储原始时间序列数据

### 2.1 设计原则

- 前端不直接感知底层表结构差异
- 后端返回面向页面的聚合结果，而不是生吐数据库字段
- 指标口径统一在后端计算，避免前后端重复实现

## 3. 前后端目录结构

```text
financial-dashboard/
├── docs/
│   ├── PRD.md
│   └── Technical-Design.md
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── App.tsx
│   │   │   ├── providers.tsx
│   │   │   └── routes.tsx
│   │   ├── pages/
│   │   │   └── dashboard/
│   │   │       └── DashboardPage.tsx
│   │   ├── features/
│   │   │   ├── sentiment/
│   │   │   │   ├── api.ts
│   │   │   │   ├── hooks.ts
│   │   │   │   ├── types.ts
│   │   │   │   └── components/
│   │   │   └── valuation/
│   │   │       ├── api.ts
│   │   │       ├── hooks.ts
│   │   │       ├── types.ts
│   │   │       └── components/
│   │   ├── components/
│   │   │   ├── charts/
│   │   │   ├── layout/
│   │   │   └── ui/
│   │   ├── lib/
│   │   └── styles/
│   └── package.json
└── backend/
    ├── app/
    │   ├── main.py
    │   ├── core/
    │   ├── api/v1/
    │   ├── schemas/
    │   ├── services/
    │   ├── repositories/
    │   └── utils/
    ├── tests/
    └── requirements.txt
```

### 3.1 前端模块拆分

#### `pages/dashboard`

负责页面骨架编排，只做布局。

#### `features/sentiment`

负责：

- Fear & Greed
- VIX
- 波动率结构
- Breadth

#### `features/valuation`

负责：

- SPX 估值卡
- NDX 估值卡
- 时间窗切换逻辑

#### `components/charts`

负责复用图表：

- `GaugeChart`
- `Sparkline`

### 3.2 后端模块拆分

#### `repositories`

职责：

- 执行 SQL
- 只返回原始行数据或最轻量 DTO

建议文件：

- `raw_fng_repository.py`
- `raw_vix_repository.py`
- `market_breadth_repository.py`
- `index_valuation_repository.py`

#### `services`

职责：

- 派生指标计算
- 标准化字段映射
- 分位数计算
- 时间窗切片

建议文件：

- `sentiment_service.py`
- `valuation_service.py`
- `mapping_service.py`

#### `api/v1`

职责：

- 参数校验
- 路由编排
- Response Schema 输出

## 4. 数据表映射

本项目直接使用现有四张业务相关表。

### 4.1 `raw_fng`

来源文件：[raw_fng.sql](/Users/lucasgou/Desktop/projects/financial-dashboard/raw_fng.sql)

真实字段：

- `trade_date`
- `fng_value`
- `updated_at`

应用层用途：

- 首页 Fear & Greed 当前值
- Fear & Greed 30 天时间序列

应用层派生字段：

- `label`
- `color`
- `day_change`

### 4.2 `raw_vix`

来源文件：[raw_vix.sql](/Users/lucasgou/Desktop/projects/financial-dashboard/raw_vix.sql)

真实字段：

- `trade_date`
- `vix_close`
- `vvix_close`
- `updated_at`

应用层用途：

- VIX 当前值
- VIX 时间序列
- 波动率结构时间序列

应用层派生字段：

- `vol_structure = vvix_close / vix_close / 3.5`

### 4.3 `market_breadth`

来源文件：[market_breadth.sql](/Users/lucasgou/Desktop/projects/financial-dashboard/market_breadth.sql)

真实字段：

- `trade_date`
- `index_name`
- `above_20d_pct`
- `above_50d_pct`
- `above_200d_pct`
- `updated_at`

应用层用途：

- SPX Breadth Card
- NDX Breadth Card

标准化映射：

- `SP500` -> `SPX`
- `NDX100` -> `NDX`

展示名映射：

- `SPX` -> `S&P 500`
- `NDX` -> `NASDAQ 100`

### 4.4 `index_valuation`

来源文件：[index_valuation.sql](/Users/lucasgou/Desktop/projects/financial-dashboard/index_valuation.sql)

真实字段：

- `trade_date`
- `index_name`
- `pe_ntm`
- `updated_at`

应用层用途：

- SPX Valuation Card
- NDX Valuation Card

### 4.5 估值名称标准化策略

`index_valuation.index_name` 是原始名称字段，不应直接暴露给前端。后端需要将其标准化为应用层代码。

当前设计口径：

- `SPX`
  - display name: `S&P 500`
- `NDX`
  - display name: `NASDAQ-100`

建议匹配规则：

```text
SPX:
- S&P 500
- SP500
- SPX
- S&P 500 Index

NDX:
- NASDAQ-100
- NASDAQ 100
- Nasdaq 100
- NDX
- NDX100
```

排除项：

- 板块/行业/主题序列
- 与宽基无关的估值记录

说明：

最终匹配白名单应以真实 `SELECT DISTINCT index_name` 结果收敛，当前文档是应用层设计草案。

## 5. 标准化字段设计

为了让前端逻辑简单，后端返回统一字段命名。

### 5.1 通用字段

- `as_of_date`
- `trade_date`
- `value`
- `series`
- `display_name`
- `index_code`

### 5.2 Fear & Greed 返回标准

```text
value
label
color
as_of_date
day_change
```

### 5.3 Breadth 返回标准

```text
index_code
display_name
as_of_date
above_20d_pct
above_50d_pct
above_200d_pct
```

### 5.4 Valuation 返回标准

```text
index_code
display_name
window
as_of_date
current_value
percentile
series[]
```

## 6. API 设计

统一前缀：

- `/api/v1`

### 6.1 `GET /api/v1/sentiment/overview`

用途：

- 聚合首屏情绪模块的当前值

数据来源：

- `raw_fng`
- `raw_vix`
- `market_breadth`

返回结构：

```json
{
  "fear_greed": {
    "as_of_date": "2026-04-18",
    "value": 21,
    "label": "Fear",
    "color": "green",
    "day_change": -3
  },
  "vix": {
    "as_of_date": "2026-04-18",
    "value": 18.32
  },
  "vol_structure": {
    "as_of_date": "2026-04-18",
    "value": 1.87
  },
  "breadth": {
    "spx": {
      "as_of_date": "2026-04-18",
      "above_20d_pct": 82.0,
      "above_50d_pct": 65.0,
      "above_200d_pct": 75.0
    },
    "ndx": {
      "as_of_date": "2026-04-18",
      "above_20d_pct": 15.0,
      "above_50d_pct": 45.0,
      "above_200d_pct": 60.0
    }
  }
}
```

### 6.2 `GET /api/v1/sentiment/fear-greed/trend?range=30d`

用途：

- Fear & Greed 卡片底部 sparkline

查询口径：

- 取最近 `30` 个交易日
- 输出升序

返回结构：

```json
{
  "range": "30d",
  "series": [
    { "trade_date": "2026-03-06", "value": 31 },
    { "trade_date": "2026-03-07", "value": 28 }
  ]
}
```

### 6.3 `GET /api/v1/sentiment/volatility/trend?range=30d`

用途：

- 同时支撑 VIX 和波动率结构 sparkline

查询口径：

- 从 `raw_vix` 取最近 `30` 个交易日
- 后端实时计算 `vol_structure`

返回结构：

```json
{
  "range": "30d",
  "vix_series": [
    { "trade_date": "2026-03-06", "value": 17.85 }
  ],
  "vol_structure_series": [
    { "trade_date": "2026-03-06", "value": 1.91 }
  ]
}
```

### 6.4 `GET /api/v1/sentiment/breadth`

用途：

- 返回两个 Breadth 卡片的最新值

查询口径：

- `market_breadth` 中按 `index_name` 分组取最新日期

返回结构：

```json
{
  "spx": {
    "index_code": "SPX",
    "display_name": "S&P 500",
    "as_of_date": "2026-04-18",
    "above_20d_pct": 82.0,
    "above_50d_pct": 65.0,
    "above_200d_pct": 75.0
  },
  "ndx": {
    "index_code": "NDX",
    "display_name": "NASDAQ 100",
    "as_of_date": "2026-04-18",
    "above_20d_pct": 15.0,
    "above_50d_pct": 45.0,
    "above_200d_pct": 60.0
  }
}
```

### 6.5 `GET /api/v1/valuation/timeline?index=SPX&window=1y`

用途：

- 支撑估值卡时间线和分位数

请求参数：

- `index`
  - `SPX`
  - `NDX`
- `window`
  - `1y`
  - `5y`
  - `10y`

查询逻辑：

1. 将 `index` 映射到允许的 `index_name` 白名单
2. 按时间窗取数据
3. 输出升序时间序列
4. 使用该窗口内数据计算当前值分位数

返回结构：

```json
{
  "index_code": "SPX",
  "display_name": "S&P 500",
  "window": "1y",
  "as_of_date": "2026-04-18",
  "current_value": 18.4,
  "percentile": 76.2,
  "series": [
    { "trade_date": "2025-05-01", "value": 17.2 },
    { "trade_date": "2025-06-01", "value": 17.4 }
  ]
}
```

### 6.6 可选聚合接口 `GET /api/v1/valuation/overview`

用途：

- 首屏同时获取 SPX 和 NDX 当前估值摘要

返回内容：

- `current_value`
- `percentile_1y`
- `percentile_5y`
- `percentile_10y`
- `as_of_date`

说明：

如果前端已按卡片单独请求，可不做此接口；如果追求更少请求数，可增加。

## 7. 状态管理

### 7.1 前端状态范围

前端只维护展示状态，不存业务主状态。

需要维护的状态：

- `valuation window`
  - `1y / 5y / 10y`
- 局部 loading 状态
- 局部 error 状态
- hover 状态

### 7.2 状态管理建议

当前项目无需复杂全局状态库。建议使用：

- React Query 或 SWR 处理服务端数据缓存
- React local state 处理卡片级交互状态

推荐规则：

- 首屏 overview 数据独立缓存
- valuation timeline 按 `index + window` 作为 cache key
- sparkline 请求可单独缓存

### 7.3 不建议的做法

- 不要把所有 API 返回复制进全局 store
- 不要在前端重复计算分位数
- 不要让前端维护数据库字段映射关系

## 8. 查询口径

### 8.1 时间粒度

当前所有已知表都按 `date` 粒度组织，项目统一使用交易日/日级数据。

### 8.2 Fear & Greed

#### 当前值

- 取 `raw_fng` 最新 `trade_date`

#### 30 天趋势

- 取最近 `30` 个交易日
- 接口返回时按升序排序

#### 日变化

- 用最近两条记录计算：
  - `latest - previous`

### 8.3 VIX 与波动率结构

#### 当前值

- 取 `raw_vix` 最新 `trade_date`

#### 趋势

- 取最近 `30` 个交易日

#### 波动率结构

- `vvix_close / vix_close / 3.5`
- 若 `vix_close` 为 `0` 或空，则该值为 `null`

### 8.4 Market Breadth

#### 最新值

- 对每个 `index_name` 取最新日期记录

#### 标准化

- `SP500` -> `SPX`
- `NDX100` -> `NDX`

#### 返回规则

- 不展开成单独 20D/50D/200D 行
- 保持宽结构，直接支撑卡片显示

### 8.5 Valuation

#### 目标序列

仅保留宽基指数：

- `SPX`
- `NDX`

#### 时间窗定义

- `1y`
  - 最近 12 个月数据
- `5y`
  - 最近 60 个月数据
- `10y`
  - 最近 120 个月数据

说明：

若数据库数据并非严格月频，则仍以“时间范围”截取，而不是硬编码条数。

#### 当前值

- 所选 index 在最新日期的 `pe_ntm`

#### 分位数

分位数计算方式：

1. 获取窗口内全部 `pe_ntm`
2. 从小到大排序
3. 计算当前值在序列中的位置百分比

分位结果用于前端颜色编码，不在前端重复计算。

硬性口径要求：

- 分位数必须基于查询出的完整窗口原始样本计算
- 不读取数据库中的预存分位字段
- 不使用手工维护的阈值近似替代
- 不在前端计算分位数

实现含义：

- `1y` 分位数：先取该指数最近 1 年窗口内全部 `pe_ntm`，再计算当前值分位
- `5y` 分位数：先取该指数最近 5 年窗口内全部 `pe_ntm`，再计算当前值分位
- `10y` 分位数：先取该指数最近 10 年窗口内全部 `pe_ntm`，再计算当前值分位

## 9. 错误处理与降级

### 9.1 后端

- 查询不到数据时返回空结构或空数组，不返回 500
- 参数非法时返回 400
- 数据源不可用时返回 503

### 9.2 前端

- 卡片级错误不影响整页其他模块显示
- 单张卡片失败时显示简洁错误占位
- 空数据使用 `No data`

## 10. 性能与缓存

### 10.1 后端

当前数据量按日级时间序列，压力不会大。第一版不需要额外缓存层。

建议：

- 关键查询加索引校验
- 使用连接池
- 控制时间窗查询范围

### 10.2 前端

建议缓存策略：

- overview：短时缓存
- trend：短时缓存
- valuation timeline：按 `index + window` 缓存

## 11. 配置与安全

当前仓库中存在真实数据库配置文件：[.db.env](/Users/lucasgou/Desktop/projects/financial-dashboard/.db.env)

工程建议：

- 将真实凭据移出版本库
- 仓库内仅保留 `.env.example`
- 后端从环境变量读取：
  - `DB_HOST`
  - `DB_PORT`
  - `DB_USER`
  - `DB_PASSWORD`
  - `DB_NAME`

## 12. 交付顺序建议

建议按以下顺序落地：

1. 后端先打通数据库连接与 5 条核心接口
2. 前端按原型拆出页面和卡片组件
3. 接入真实 API，替换 mock 数据
4. 补异常态和移动端适配

第一阶段最小可交付范围：

- `/sentiment/overview`
- `/sentiment/fear-greed/trend`
- `/sentiment/volatility/trend`
- `/sentiment/breadth`
- `/valuation/timeline`
