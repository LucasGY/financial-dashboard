# 回测数据层说明

## 目标

在当前 MariaDB 数据库 `finance` 中新增股票回测原始数据表，覆盖：

- `SPY`
- `QQQ`
- `BRK-B`
- `AAPL`
- `MSFT`
- `AMZN`
- `GOOGL`
- `META`
- `NVDA`
- `TSLA`

股票侧只存自 `2000-01-01` 起的日频 `Adj Close`。  
波动率因子继续复用现有的 `finance.raw_vix`，其中包含：

- `vix_close`
- `vvix_close`

`RSI`、均线、收益率、滚动波动率等技术指标不入库，统一在回测程序里按参数动态计算。

## 新增表

DDL 文件：

- [dim_instrument.sql](/Users/lucasgou/Desktop/projects/financial-dashboard/dim_instrument.sql)
- [raw_equity_daily_price.sql](/Users/lucasgou/Desktop/projects/financial-dashboard/raw_equity_daily_price.sql)

表职责：

- `dim_instrument`
  - 证券主数据
  - 对 `ticker` 做唯一约束
- `raw_equity_daily_price`
  - 每日复权收盘价事实表
  - 以 `(instrument_id, trade_date)` 为主键
  - 幂等支持 `ON DUPLICATE KEY UPDATE`

## 抓数脚本

脚本位置：

- [backfill_equity_prices.py](/Users/lucasgou/Desktop/projects/financial-dashboard/backend/scripts/backfill_equity_prices.py)
- [sync_equity_prices_daily.py](/Users/lucasgou/Desktop/projects/financial-dashboard/backend/scripts/sync_equity_prices_daily.py)

依赖：

```bash
cd /Users/lucasgou/Desktop/projects/financial-dashboard
./.venv/bin/pip install -r backend/requirements.txt
```

首次建表：

```bash
cd /Users/lucasgou/Desktop/projects/financial-dashboard
./.venv/bin/python - <<'PY'
from pathlib import Path
import pymysql
import sys

sys.path.insert(0, str(Path('backend').resolve()))

from app.core.config import get_settings

settings = get_settings()

sql_files = [Path('dim_instrument.sql'), Path('raw_equity_daily_price.sql')]

conn = pymysql.connect(
    host=settings.mariadb_host,
    port=settings.mariadb_port,
    user=settings.mariadb_user,
    password=settings.mariadb_password,
    database=settings.mariadb_database,
    autocommit=True,
)
with conn.cursor() as cur:
    for path in sql_files:
        cur.execute(path.read_text())
conn.close()
PY
```

历史回填：

```bash
cd /Users/lucasgou/Desktop/projects/financial-dashboard/backend
../.venv/bin/python scripts/backfill_equity_prices.py --start 2000-01-01
```

每日增量：

```bash
cd /Users/lucasgou/Desktop/projects/financial-dashboard/backend
../.venv/bin/python scripts/sync_equity_prices_daily.py --lookback-days 10
```

脚本行为：

- 数据源固定为 `Yahoo / yfinance`
- 每个 ticker 单独下载，避免单个失败拖垮整批任务
- 只写入非空 `Adj Close`
- 自动 upsert `dim_instrument`
- 自动 upsert `raw_equity_daily_price`
- 输出成功 ticker、失败 ticker、下载行数、入库影响行数

## 回测读取示例

```sql
SELECT
  p.trade_date,
  i.ticker,
  p.adj_close_price,
  v.vix_close,
  v.vvix_close
FROM raw_equity_daily_price p
INNER JOIN dim_instrument i
  ON i.instrument_id = p.instrument_id
LEFT JOIN raw_vix v
  ON v.trade_date = p.trade_date
WHERE i.ticker IN ('SPY', 'QQQ', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NVDA', 'TSLA')
  AND p.trade_date >= '2000-01-01'
ORDER BY p.trade_date, i.ticker;
```

如果把伯克希尔也纳入股票池，查询条件改为：

```sql
WHERE i.ticker IN ('SPY', 'QQQ', 'BRK-B', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NVDA', 'TSLA')
  AND p.trade_date >= '2000-01-01'
ORDER BY p.trade_date, i.ticker;
```

回测程序拿到这份结果后，按 `ticker` 分组并按 `trade_date` 排序，再动态计算：

- `RSI(2)`
- `RSI(14)`
- `RSI(21)`
- `SMA(20 / 50 / 200)`
- 收益率
- 滚动波动率

## 约束与取舍

- 第一阶段不改现有 FastAPI API 层
- 第一阶段不把 `raw_fng` 纳入核心表设计
- 第一阶段不存 OHLCV、分红、拆股明细
- `finance.raw_vix` 继续保持现有单表结构
