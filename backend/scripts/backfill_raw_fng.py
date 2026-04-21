from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys

import pandas as pd
import pymysql

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings

FNG_DATA_URL = "https://raw.githubusercontent.com/whit3rabbit/fear-greed-data/main/fear-greed.csv"
FNG_FALLBACK_URL = "https://raw.githubusercontent.com/gman4774/Fear_and_Greed_Index/master/all_fng_csv.csv"


@dataclass(frozen=True)
class FngRow:
    trade_date: object
    fng_value: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill Fear & Greed history into raw_fng.",
    )
    parser.add_argument(
        "--start",
        default="2011-01-03",
        help="Inclusive start date in YYYY-MM-DD.",
    )
    parser.add_argument(
        "--end",
        default=None,
        help="Inclusive end date in YYYY-MM-DD. Default: use all available rows.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Rows per SQL batch.",
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


def fetch_spy_trading_dates(connection: pymysql.connections.Connection, start: str, end: str | None) -> set:
    query = """
        SELECT p.trade_date
        FROM raw_equity_daily_price p
        JOIN dim_instrument i ON i.instrument_id = p.instrument_id
        WHERE i.ticker = 'SPY'
          AND p.trade_date >= %s
    """
    params: list[object] = [start]
    if end:
        query += " AND p.trade_date <= %s"
        params.append(end)
    query += " ORDER BY p.trade_date"
    with connection.cursor() as cursor:
        cursor.execute(query, tuple(params))
        return {row[0] for row in cursor.fetchall()}


def normalize_value(value: object) -> int | None:
    if value is None or pd.isna(value):
        return None
    return int(round(float(value)))


def load_frame(url: str) -> pd.DataFrame:
    frame = pd.read_csv(url)
    if "Date" not in frame.columns or "Fear Greed" not in frame.columns:
        raise RuntimeError(f"Unexpected Fear & Greed dataset columns from {url}.")
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce").dt.date
    frame["Fear Greed"] = pd.to_numeric(frame["Fear Greed"], errors="coerce")
    frame = frame.dropna(subset=["Date", "Fear Greed"])
    return frame[["Date", "Fear Greed"]]


def load_rows(connection: pymysql.connections.Connection, start: str, end: str | None) -> list[FngRow]:
    primary = load_frame(FNG_DATA_URL)
    fallback = load_frame(FNG_FALLBACK_URL)

    merged = primary.rename(columns={"Fear Greed": "primary_value"}).merge(
        fallback.rename(columns={"Fear Greed": "fallback_value"}),
        on="Date",
        how="outer",
    )
    merged["Fear Greed"] = merged["primary_value"].combine_first(merged["fallback_value"])
    merged = merged[["Date", "Fear Greed"]]
    merged = merged[merged["Date"] >= pd.Timestamp(start).date()]
    if end:
        merged = merged[merged["Date"] <= pd.Timestamp(end).date()]

    spy_trading_dates = fetch_spy_trading_dates(connection, start, end)
    merged = merged[merged["Date"].isin(spy_trading_dates)]
    merged = merged.sort_values("Date")

    rows: list[FngRow] = []
    for _, item in merged.iterrows():
        value = normalize_value(item["Fear Greed"])
        if value is None:
            continue
        rows.append(FngRow(trade_date=item["Date"], fng_value=value))
    return rows


def chunked(values: list[tuple], size: int) -> list[list[tuple]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def upsert_rows(connection: pymysql.connections.Connection, rows: list[FngRow], batch_size: int) -> int:
    if not rows:
        return 0

    sql_prefix = """
        INSERT IGNORE INTO raw_fng (
            trade_date,
            fng_value
        )
        VALUES
    """
    payload = [(row.trade_date, row.fng_value) for row in rows]

    affected_rows = 0
    with connection.cursor() as cursor:
        for batch in chunked(payload, batch_size):
            placeholders = ", ".join(["(%s, %s)"] * len(batch))
            flat_params: list[object] = []
            for row in batch:
                flat_params.extend(row)
            cursor.execute(sql_prefix + placeholders, tuple(flat_params))
            affected_rows += cursor.rowcount
    return affected_rows


def main() -> None:
    args = parse_args()
    with get_connection() as connection:
        rows = load_rows(connection=connection, start=args.start, end=args.end)
        affected_rows = upsert_rows(connection, rows, args.batch_size)

    print(f"Backfill completed: {args.start} -> {args.end or 'all available'}")
    print(f"Primary source: {FNG_DATA_URL}")
    print(f"Fallback source: {FNG_FALLBACK_URL}")
    print(f"Downloaded rows: {len(rows)}")
    print(f"Affected rows: {affected_rows}")


if __name__ == "__main__":
    main()
