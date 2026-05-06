from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import time
import sys

import pandas as pd
import pymysql
from tvDatafeed import Interval, TvDatafeed

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings

FIELD_MAP = {
    "20d": "above_20d_pct",
    "50d": "above_50d_pct",
    "200d": "above_200d_pct",
}


@dataclass(frozen=True)
class IndexConfig:
    index_name: str
    symbols: dict[str, str]


INDEX_CONFIGS = {
    "NDX100": IndexConfig(
        index_name="NDX100",
        symbols={
            "NDTW": FIELD_MAP["20d"],
            "NDFI": FIELD_MAP["50d"],
            "NDTH": FIELD_MAP["200d"],
        },
    ),
    "SP500": IndexConfig(
        index_name="SP500",
        symbols={
            "S5TW": FIELD_MAP["20d"],
            "S5FI": FIELD_MAP["50d"],
            "S5TH": FIELD_MAP["200d"],
        },
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill market_breadth from TradingView breadth symbols.",
    )
    parser.add_argument(
        "--start",
        default="2000-01-01",
        help="Inclusive start date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--end",
        default=None,
        help="Inclusive end date in YYYY-MM-DD format. Defaults to latest available.",
    )
    parser.add_argument(
        "--n-bars",
        type=int,
        default=5000,
        help="Number of daily bars to request from TradingView per symbol.",
    )
    parser.add_argument(
        "--username",
        default=None,
        help="Optional TradingView username. Omit to use TvDatafeed no-login mode.",
    )
    parser.add_argument(
        "--password",
        default=None,
        help="Optional TradingView password. Omit to use TvDatafeed no-login mode.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Rows per SQL batch.",
    )
    parser.add_argument(
        "--index-name",
        action="append",
        choices=sorted(INDEX_CONFIGS.keys()),
        dest="index_names",
        help="Index to backfill. Repeat to load multiple. Defaults to all configured indexes.",
    )
    return parser.parse_args()


def get_connection() -> pymysql.connections.Connection:
    settings = get_settings()
    return pymysql.connect(
        host=settings.mariadb_host,
        port=settings.mariadb_port,
        user=settings.mariadb_user,
        password=settings.mariadb_password,
        database=settings.mariadb_database,
        autocommit=True,
    )


def build_tv_client(username: str | None, password: str | None) -> TvDatafeed:
    if username and password:
        return TvDatafeed(username, password)
    return TvDatafeed()


def fetch_symbol_series(
    symbol: str,
    field_name: str,
    n_bars: int,
    username: str | None,
    password: str | None,
    attempts: int = 3,
    retry_delay_seconds: float = 1.0,
) -> pd.Series:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            tv = build_tv_client(username, password)
            frame = tv.get_hist(
                symbol=symbol,
                exchange="INDEX",
                interval=Interval.in_daily,
                n_bars=n_bars,
            )
            if frame is None or frame.empty:
                raise RuntimeError(f"No data returned for INDEX:{symbol}")
            series = frame["close"].copy()
            series.index = pd.to_datetime(series.index).date
            return series.rename(field_name)
        except Exception as exc:
            last_error = exc
            if attempt == attempts:
                break
            time.sleep(retry_delay_seconds)
    raise RuntimeError(f"Failed to fetch INDEX:{symbol}") from last_error


def load_market_breadth_frame(
    config: IndexConfig,
    n_bars: int,
    username: str | None,
    password: str | None,
) -> pd.DataFrame:
    series_list = [
        fetch_symbol_series(symbol, field_name, n_bars, username, password)
        for symbol, field_name in config.symbols.items()
    ]
    frame = pd.concat(series_list, axis=1).sort_index()
    frame.index.name = "trade_date"
    frame = frame.reset_index()
    frame["trade_date"] = pd.to_datetime(frame["trade_date"]).dt.date
    frame["index_name"] = config.index_name
    ordered_columns = [
        "trade_date",
        "index_name",
        "above_20d_pct",
        "above_50d_pct",
        "above_200d_pct",
    ]
    frame = frame[ordered_columns]
    return frame.dropna(
        subset=["above_20d_pct", "above_50d_pct", "above_200d_pct"],
        how="all",
    )


def filter_frame(frame: pd.DataFrame, start: str, end: str | None) -> pd.DataFrame:
    start_date = pd.Timestamp(start).date()
    filtered = frame[frame["trade_date"] >= start_date].copy()
    if end:
        end_date = pd.Timestamp(end).date()
        filtered = filtered[filtered["trade_date"] <= end_date].copy()
    return filtered.sort_values("trade_date").reset_index(drop=True)


def chunked(values: list[tuple], size: int) -> list[list[tuple]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def summarize_existing_overlap(connection: pymysql.connections.Connection, frame: pd.DataFrame, index_name: str) -> None:
    if frame.empty:
        print(f"{index_name} overlap rows: 0")
        return

    start_date = frame["trade_date"].min()
    end_date = frame["trade_date"].max()
    query = """
        SELECT trade_date, above_20d_pct, above_50d_pct, above_200d_pct
        FROM market_breadth
        WHERE index_name = %s
          AND trade_date BETWEEN %s AND %s
        ORDER BY trade_date
    """
    with connection.cursor() as cursor:
        cursor.execute(query, (index_name, start_date, end_date))
        existing_rows = cursor.fetchall()

    if not existing_rows:
        print(f"{index_name} overlap rows: 0")
        return

    existing = pd.DataFrame(
        existing_rows,
        columns=["trade_date", "db_above_20d_pct", "db_above_50d_pct", "db_above_200d_pct"],
    )
    merged = frame.merge(existing, on="trade_date", how="inner")
    if merged.empty:
        print(f"{index_name} overlap rows: 0")
        return

    numeric_columns = [
        "above_20d_pct",
        "db_above_20d_pct",
        "above_50d_pct",
        "db_above_50d_pct",
        "above_200d_pct",
        "db_above_200d_pct",
    ]
    for column in numeric_columns:
        merged[column] = pd.to_numeric(merged[column], errors="coerce")

    def count_diffs(left: str, right: str) -> int:
        both = merged[left].notna() & merged[right].notna()
        return int((merged.loc[both, left].round(2) != merged.loc[both, right].round(2)).sum())

    print(f"{index_name} overlap rows: {len(merged)}")
    print(
        f"{index_name} diffs: "
        f"20d={count_diffs('above_20d_pct', 'db_above_20d_pct')}, "
        f"50d={count_diffs('above_50d_pct', 'db_above_50d_pct')}, "
        f"200d={count_diffs('above_200d_pct', 'db_above_200d_pct')}"
    )
    sample = merged[
        (
            merged["above_20d_pct"].round(2) != merged["db_above_20d_pct"].round(2)
        ) | (
            merged["above_50d_pct"].round(2) != merged["db_above_50d_pct"].round(2)
        ) | (
            merged["above_200d_pct"].round(2) != merged["db_above_200d_pct"].round(2)
        )
    ][
        [
            "trade_date",
            "above_20d_pct",
            "db_above_20d_pct",
            "above_50d_pct",
            "db_above_50d_pct",
            "above_200d_pct",
            "db_above_200d_pct",
        ]
    ].head(5)
    if not sample.empty:
        print(sample.to_string(index=False))


def upsert_rows(connection: pymysql.connections.Connection, frame: pd.DataFrame, batch_size: int) -> int:
    if frame.empty:
        return 0

    sql_prefix = """
        INSERT INTO market_breadth (
            trade_date,
            index_name,
            above_20d_pct,
            above_50d_pct,
            above_200d_pct
        )
        VALUES
    """
    sql_suffix = """
        ON DUPLICATE KEY UPDATE
            above_20d_pct = COALESCE(VALUES(above_20d_pct), above_20d_pct),
            above_50d_pct = COALESCE(VALUES(above_50d_pct), above_50d_pct),
            above_200d_pct = COALESCE(VALUES(above_200d_pct), above_200d_pct)
    """
    payload = [
        (
            row.trade_date,
            row.index_name,
            None if pd.isna(row.above_20d_pct) else float(row.above_20d_pct),
            None if pd.isna(row.above_50d_pct) else float(row.above_50d_pct),
            None if pd.isna(row.above_200d_pct) else float(row.above_200d_pct),
        )
        for row in frame.itertuples(index=False)
    ]

    affected_rows = 0
    with connection.cursor() as cursor:
        for batch in chunked(payload, batch_size):
            placeholders = ", ".join(["(%s, %s, %s, %s, %s)"] * len(batch))
            flat_params: list[object] = []
            for row in batch:
                flat_params.extend(row)
            cursor.execute(sql_prefix + placeholders + sql_suffix, tuple(flat_params))
            affected_rows += cursor.rowcount
    return affected_rows


def main() -> None:
    args = parse_args()
    index_names = args.index_names or sorted(INDEX_CONFIGS.keys())

    with get_connection() as connection:
        for index_name in index_names:
            config = INDEX_CONFIGS[index_name]
            frame = load_market_breadth_frame(config, args.n_bars, args.username, args.password)
            frame = filter_frame(frame, args.start, args.end)
            summarize_existing_overlap(connection, frame, index_name)
            affected_rows = upsert_rows(connection, frame, args.batch_size)

            print(f"Index name: {index_name}")
            print("TradingView symbols: " + ", ".join(f"INDEX:{symbol}" for symbol in config.symbols))
            print(f"Loaded rows: {len(frame)}")
            print(f"Affected rows: {affected_rows}")
            if not frame.empty:
                print(f"Date range: {frame['trade_date'].min()} -> {frame['trade_date'].max()}")


if __name__ == "__main__":
    main()
