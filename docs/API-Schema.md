# Financial Dashboard API Schema

## 1. 文档范围

本文定义 Financial Dashboard 后端 API 的字段级契约，目标是让前端和后端在实现前就统一以下内容：

- 接口路径
- 请求参数
- 响应字段
- 字段类型
- 字段含义
- 错误返回格式

统一约定：

- Base URL: `/api/v1`
- Content-Type: `application/json`
- 时间字段统一使用 `YYYY-MM-DD`
- 数值字段默认返回 JSON number，不返回字符串数字
- 响应字段优先使用 snake_case
- 数值精度由后端固定：
  - `raw_vix` / `market_breadth` 来源字段保留到小数点后 2 位
  - `index_valuation.pe_ntm` 保留到小数点后 4 位
  - `vol_structure` 保留到小数点后 4 位
  - 原始值为 `null` 时返回 `null`

## 2. 通用响应约定

### 2.1 成功响应

成功响应直接返回业务对象，不额外包裹 `data`。

### 2.2 错误响应

所有错误响应统一格式：

```json
{
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "window must be one of: 1y, 5y, 10y"
  }
}
```

字段说明：

- `error.code`
  - 错误码，供前端程序判断
- `error.message`
  - 人类可读错误信息

### 2.3 常用错误码

- `INVALID_PARAMETER`
- `NOT_FOUND`
- `DATA_UNAVAILABLE`
- `INTERNAL_ERROR`

## 3. 通用数据类型

### 3.1 `TimeSeriesPoint`

用于所有时间序列接口。

```json
{
  "trade_date": "2026-04-18",
  "value": 18.42
}
```

字段：

- `trade_date` `string`
  - 交易日期
- `value` `number | null`
  - 数值；若无法计算可为 `null`

### 3.2 `BreadthSnapshot`

```json
{
  "index_code": "SPX",
  "display_name": "S&P 500",
  "as_of_date": "2026-04-18",
  "above_20d_pct": 82.0,
  "above_50d_pct": 65.0,
  "above_200d_pct": 75.0
}
```

字段：

- `index_code` `string`
  - 标准化指数代码，允许值：`SPX`、`NDX`
- `display_name` `string`
  - 前端展示名
- `as_of_date` `string`
  - 数据日期
- `above_20d_pct` `number | null`
- `above_50d_pct` `number | null`
- `above_200d_pct` `number | null`

## 4. Market Sentiment APIs

## 4.1 `GET /api/v1/sentiment/overview`

### 4.1.1 用途

首屏聚合接口，一次返回情绪模块所有当前值。

### 4.1.2 请求参数

无。

### 4.1.3 响应结构

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
      "index_code": "SPX",
      "display_name": "S&P 500",
      "as_of_date": "2026-04-18",
      "above_20d_pct": 82.0,
      "above_50d_pct": 65.0,
      "above_200d_pct": 75.0
    },
    "ndx": {
      "index_code": "NDX",
      "display_name": "NASDAQ-100",
      "as_of_date": "2026-04-18",
      "above_20d_pct": 15.0,
      "above_50d_pct": 45.0,
      "above_200d_pct": 60.0
    }
  }
}
```

### 4.1.4 字段定义

#### `fear_greed`

- `as_of_date` `string`
  - 最新 `raw_fng.trade_date`
- `value` `integer | null`
  - `raw_fng.fng_value`
- `label` `string | null`
  - 后端映射得到的状态标签
  - 允许值：
    - `Extreme Fear`
    - `Fear`
    - `Neutral`
    - `Greed`
    - `Extreme Greed`
- `color` `string | null`
  - 前端语义色标识
  - 允许值建议：
    - `dark_green`
    - `green`
    - `neutral`
    - `orange`
    - `red`
- `day_change` `number | null`
  - 最近两条数据的差值

#### `vix`

- `as_of_date` `string`
  - 最新 `raw_vix.trade_date`
- `value` `number | null`
  - `raw_vix.vix_close`

#### `vol_structure`

- `as_of_date` `string`
- `value` `number | null`
  - `vvix_close / vix_close / 3.5`

#### `breadth`

- `spx` `BreadthSnapshot | null`
- `ndx` `BreadthSnapshot | null`

### 4.1.5 数据来源

- `fear_greed` -> `raw_fng`
- `vix` -> `raw_vix`
- `vol_structure` -> `raw_vix`
- `breadth` -> `market_breadth`

### 4.1.6 错误

- `503 DATA_UNAVAILABLE`
  - 数据源不可访问

## 4.2 `GET /api/v1/sentiment/fear-greed/trend`

### 4.2.1 用途

返回 Fear & Greed 走势图。

### 4.2.2 请求参数

Query params:

- `range` `string` optional
  - 默认：`30d`
  - 当前允许值：
    - `30d`

示例：

`GET /api/v1/sentiment/fear-greed/trend?range=30d`

### 4.2.3 响应结构

```json
{
  "range": "30d",
  "as_of_date": "2026-04-18",
  "start_value": 31,
  "end_value": 21,
  "min_value": 18,
  "max_value": 39,
  "series": [
    { "trade_date": "2026-03-20", "value": 31 },
    { "trade_date": "2026-03-21", "value": 30 }
  ]
}
```

### 4.2.4 字段定义

- `range` `string`
- `as_of_date` `string | null`
  - 序列最后一个交易日
- `start_value` `number | null`
  - 序列首值
- `end_value` `number | null`
  - 序列末值
- `min_value` `number | null`
- `max_value` `number | null`
- `series` `TimeSeriesPoint[]`

### 4.2.5 错误

- `400 INVALID_PARAMETER`
  - `range` 非法

## 4.3 `GET /api/v1/sentiment/volatility/trend`

### 4.3.1 用途

返回 VIX 与波动率结构时间序列。

### 4.3.2 请求参数

Query params:

- `range` `string` optional
  - 默认：`30d`
  - 当前允许值：
    - `30d`

示例：

`GET /api/v1/sentiment/volatility/trend?range=30d`

### 4.3.3 响应结构

```json
{
  "range": "30d",
  "as_of_date": "2026-04-18",
  "vix_current": 18.32,
  "vol_structure_current": 1.87,
  "vix_series": [
    { "trade_date": "2026-03-20", "value": 17.85 }
  ],
  "vol_structure_series": [
    { "trade_date": "2026-03-20", "value": 1.91 }
  ]
}
```

### 4.3.4 字段定义

- `range` `string`
- `as_of_date` `string | null`
- `vix_current` `number | null`
- `vol_structure_current` `number | null`
- `vix_series` `TimeSeriesPoint[]`
- `vol_structure_series` `TimeSeriesPoint[]`

### 4.3.5 计算规则

- `vix_series.value = raw_vix.vix_close`
- `vol_structure_series.value = raw_vix.vvix_close / raw_vix.vix_close / 3.5`
- 若 `vix_close` 为 `0` 或 `null`，对应 `vol_structure_series.value = null`

### 4.3.6 错误

- `400 INVALID_PARAMETER`

## 4.4 `GET /api/v1/sentiment/breadth`

### 4.4.1 用途

返回两个指数的最新 breadth 快照。

### 4.4.2 请求参数

无。

### 4.4.3 响应结构

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
    "display_name": "NASDAQ-100",
    "as_of_date": "2026-04-18",
    "above_20d_pct": 15.0,
    "above_50d_pct": 45.0,
    "above_200d_pct": 60.0
  }
}
```

### 4.4.4 字段定义

- `spx` `BreadthSnapshot | null`
- `ndx` `BreadthSnapshot | null`

### 4.4.5 映射规则

- `market_breadth.index_name = SP500` -> `spx`
- `market_breadth.index_name = NDX100` -> `ndx`

## 5. Valuation APIs

## 5.1 `GET /api/v1/valuation/timeline`

### 5.1.1 用途

返回单个指数在指定时间窗下的估值时间线和当前分位数。

### 5.1.2 请求参数

Query params:

- `index` `string` required
  - 允许值：
    - `SPX`
    - `NDX`
- `window` `string` required
  - 允许值：
    - `1y`
    - `5y`
    - `10y`

示例：

`GET /api/v1/valuation/timeline?index=SPX&window=5y`

### 5.1.3 响应结构

```json
{
  "index_code": "SPX",
  "display_name": "S&P 500",
  "window": "5y",
  "as_of_date": "2026-04-18",
  "current_value": 18.4,
  "percentile": 76.2,
  "series": [
    { "trade_date": "2021-05-01", "value": 17.2 },
    { "trade_date": "2021-06-01", "value": 17.4 }
  ]
}
```

### 5.1.4 字段定义

- `index_code` `string`
  - `SPX` 或 `NDX`
- `display_name` `string`
  - `S&P 500` 或 `NASDAQ-100`
- `window` `string`
  - `1y` / `5y` / `10y`
- `as_of_date` `string | null`
  - 当前序列的最后日期
- `current_value` `number | null`
  - 当前窗口内最后一个点的 `pe_ntm`
- `percentile` `number | null`
  - 当前值在所选窗口中的历史分位
  - 取值范围建议：`0-100`
- `series` `TimeSeriesPoint[]`

### 5.1.5 查询规则

1. 根据 `index` 做原始 `index_name` 白名单映射
2. 根据 `window` 取时间范围
3. 返回该窗口的全部时间序列
4. 以窗口内 `series.value` 计算 `percentile`

分位数硬性约束：

- `percentile` 必须在后端基于该接口本次查询出的完整窗口原始样本计算
- 不允许读取数据库预存分位字段直接返回
- 不允许在前端二次计算分位数
- 不允许使用固定阈值近似历史分位

### 5.1.6 `index` 映射

当前应用层标准映射：

- `SPX`
  - `display_name = S&P 500`
- `NDX`
  - `display_name = NASDAQ-100`

后端应在 `mapping_service` 中维护原始 `index_name` 白名单，不由前端承担。

### 5.1.7 错误

- `400 INVALID_PARAMETER`
  - `index` 或 `window` 非法
- `404 NOT_FOUND`
  - 指定 index 在窗口内无数据

## 5.2 `GET /api/v1/valuation/overview`

### 5.2.1 用途

返回两个指数的当前估值摘要，便于首屏聚合加载。

### 5.2.2 请求参数

无。

### 5.2.3 响应结构

```json
{
  "spx": {
    "index_code": "SPX",
    "display_name": "S&P 500",
    "as_of_date": "2026-04-18",
    "current_value": 18.4,
    "percentile_1y": 72.1,
    "percentile_5y": 76.2,
    "percentile_10y": 81.4
  },
  "ndx": {
    "index_code": "NDX",
    "display_name": "NASDAQ-100",
    "as_of_date": "2026-04-18",
    "current_value": 25.3,
    "percentile_1y": 68.2,
    "percentile_5y": 83.1,
    "percentile_10y": 88.0
  }
}
```

### 5.2.4 字段定义

#### `spx` / `ndx`

- `index_code` `string`
- `display_name` `string`
- `as_of_date` `string | null`
- `current_value` `number | null`
- `percentile_1y` `number | null`
- `percentile_5y` `number | null`
- `percentile_10y` `number | null`

### 5.2.5 用途说明

这个接口不是严格必须，但如果首屏想减少请求数，它有价值。

## 6. 前端消费映射

## 6.1 FearGreedCard

接口：

- `/sentiment/overview`
- `/sentiment/fear-greed/trend`

需要字段：

- `fear_greed.value`
- `fear_greed.label`
- `fear_greed.color`
- `fear_greed.as_of_date`
- `trend.series`
- `trend.start_value`
- `trend.end_value`

## 6.2 VolatilityCard

接口：

- `/sentiment/overview`
- `/sentiment/volatility/trend`

需要字段：

- `vix.value`
- `vol_structure.value`
- `vix_series`
- `vol_structure_series`

## 6.3 BreadthCard

接口：

- `/sentiment/breadth`

需要字段：

- `above_20d_pct`
- `above_50d_pct`
- `above_200d_pct`

## 6.4 ValuationCard

接口：

- `/valuation/timeline?index=SPX&window=...`
- `/valuation/timeline?index=NDX&window=...`

需要字段：

- `current_value`
- `percentile`
- `window`
- `series`

## 7. 数据库字段到 API 字段映射

## 7.1 `raw_fng`

- `trade_date` -> `fear_greed.as_of_date`
- `fng_value` -> `fear_greed.value`
- `fng_value` -> `trend.series[].value`

派生：

- `fng_value` -> `fear_greed.label`
- `fng_value` -> `fear_greed.color`
- `latest - previous` -> `fear_greed.day_change`

## 7.2 `raw_vix`

- `trade_date` -> `vix.as_of_date`
- `vix_close` -> `vix.value`
- `vix_close` -> `vix_series[].value`
- `vvix_close / vix_close / 3.5` -> `vol_structure.value`
- `vvix_close / vix_close / 3.5` -> `vol_structure_series[].value`

## 7.3 `market_breadth`

- `index_name = SP500` -> `spx`
- `index_name = NDX100` -> `ndx`
- `above_20d_pct` -> `above_20d_pct`
- `above_50d_pct` -> `above_50d_pct`
- `above_200d_pct` -> `above_200d_pct`

## 7.4 `index_valuation`

- `pe_ntm` -> `current_value`
- `pe_ntm` -> `series[].value`
- `trade_date` -> `series[].trade_date`

派生：

- `current_value 在窗口内位置` -> `percentile`

说明：

- `percentile` 的计算前提是先完整取出对应 `window` 下的全部 `pe_ntm` 原始样本
- 然后以最新值为 `current_value` 进行排序定位

## 8. 空值和异常值约定

### 8.1 空值

若原始字段为空：

- 接口返回 `null`
- 不返回空字符串

### 8.2 空序列

若查询时间窗内无数据：

- 返回 `404 NOT_FOUND`
  或
- 返回空 `series`

推荐：

- timeline 类接口使用 `404 NOT_FOUND`
- overview 类接口字段返回 `null`

### 8.3 日期缺口

若时间序列中存在非连续日期：

- 接口不补空日期
- 直接返回数据库中真实存在的交易日序列

## 9. 版本约束

V1 API 只支持以下能力：

- Fear & Greed 当前值和 30d 走势
- VIX 与波动率结构当前值和 30d 走势
- SPX/NDX Breadth 最新快照
- SPX/NDX 估值 timeline 与分位数

V1 不支持：

- 自定义日期区间
- 多指数动态枚举
- 多因子筛选
- 批量指标下载
