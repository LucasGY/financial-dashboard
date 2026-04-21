from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
import time

import pandas as pd
import pymysql
import yfinance as yf

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings

CBOE_VVIX_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VVIX_History.csv"


@dataclass(frozen=True)
class VixRow:
    trade_date: object
    vix_close: float | None
    vvix_close: float | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill VIX and VVIX close history from Yahoo Finance into raw_vix.",
    )
    parser.add_argument(
        "--start",
        default="2000-01-01",
        help="Inclusive start date in YYYY-MM-DD.",
    )
    parser.add_argument(
        "--end",
        default=None,
        help="Exclusive end date in YYYY-MM-DD. Default: today.",
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


def normalize_number(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 2)


def download_close_history(ticker: str, start: str, end: str | None, max_attempts: int = 2) -> pd.DataFrame:
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            frame = yf.download(
                tickers=ticker,
                start=start,
                end=end,
                interval="1d",
                auto_adjust=False,
                progress=False,
                threads=False,
            )
            if frame.empty:
                return pd.DataFrame(columns=["trade_date", "close_price"])
            if isinstance(frame.columns, pd.MultiIndex):
                frame = frame.droplevel("Ticker", axis=1)
            prepared = frame.reset_index().copy()
            prepared.columns = [str(column) for column in prepared.columns]
            if "Date" not in prepared.columns or "Close" not in prepared.columns:
                raise RuntimeError(f"Unexpected Yahoo Finance columns for {ticker}.")
            prepared = prepared[["Date", "Close"]].rename(
                columns={"Date": "trade_date", "Close": "close_price"}
            )
            prepared["trade_date"] = pd.to_datetime(prepared["trade_date"]).dt.date
            prepared["close_price"] = pd.to_numeric(prepared["close_price"], errors="coerce")
            prepared = prepared.dropna(subset=["close_price"])
            return prepared
        except Exception as exc:
            last_error = exc
            if attempt < max_attempts:
                time.sleep(2)
    if last_error is not None:
        raise last_error
    return pd.DataFrame(columns=["trade_date", "close_price"])


def load_cboe_vvix_history(start: str, end: str | None) -> pd.DataFrame:
    frame = pd.read_csv(CBOE_VVIX_URL)
    if "DATE" not in frame.columns or "VVIX" not in frame.columns:
        raise RuntimeError("Unexpected Cboe VVIX CSV columns.")
    frame["DATE"] = pd.to_datetime(frame["DATE"], format="%m/%d/%Y", errors="coerce").dt.date
    frame["VVIX"] = pd.to_numeric(frame["VVIX"], errors="coerce")
    frame = frame.dropna(subset=["DATE", "VVIX"])
    frame = frame.rename(columns={"DATE": "trade_date", "VVIX": "vvix_close"})
    frame = frame[frame["trade_date"] >= pd.Timestamp(start).date()]
    if end:
        exclusive_end = pd.Timestamp(end).date()
        frame = frame[frame["trade_date"] < exclusive_end]
    return frame[["trade_date", "vvix_close"]]


def build_rows(start: str, end: str | None) -> list[VixRow]:
    vix_frame = download_close_history("^VIX", start, end).rename(columns={"close_price": "vix_close"})
    vvix_cboe_frame = load_cboe_vvix_history(start, end).rename(columns={"vvix_close": "vvix_close_cboe"})
    vvix_yahoo_frame = download_close_history("^VVIX", start, end).rename(columns={"close_price": "vvix_close_yahoo"})

    merged = pd.merge(vix_frame, vvix_cboe_frame, on="trade_date", how="outer")
    merged = pd.merge(merged, vvix_yahoo_frame, on="trade_date", how="outer")
    merged["vvix_close"] = merged["vvix_close_cboe"].combine_first(merged["vvix_close_yahoo"])
    merged = merged.sort_values("trade_date")
    rows: list[VixRow] = []
    for _, item in merged.iterrows():
        rows.append(
            VixRow(
                trade_date=item["trade_date"],
                vix_close=normalize_number(item.get("vix_close")),
                vvix_close=normalize_number(item.get("vvix_close")),
            )
        )
    return rows


def chunked(values: list[tuple], size: int) -> list[list[tuple]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def upsert_rows(connection: pymysql.connections.Connection, rows: list[VixRow], batch_size: int) -> int:
    if not rows:
        return 0

    sql_prefix = """
        INSERT INTO raw_vix (
            trade_date,
            vix_close,
            vvix_close
        )
        VALUES
    """
    sql_suffix = """
        ON DUPLICATE KEY UPDATE
            vix_close = VALUES(vix_close),
            vvix_close = VALUES(vvix_close)
    """
    payload = [(row.trade_date, row.vix_close, row.vvix_close) for row in rows]

    affected_rows = 0
    with connection.cursor() as cursor:
        for batch in chunked(payload, batch_size):
            placeholders = ", ".join(["(%s, %s, %s)"] * len(batch))
            flat_params: list[object] = []
            for row in batch:
                flat_params.extend(row)
            cursor.execute(sql_prefix + placeholders + sql_suffix, tuple(flat_params))
            affected_rows += cursor.rowcount
    return affected_rows


def main() -> None:
    args = parse_args()
    rows = build_rows(start=args.start, end=args.end)
    with get_connection() as connection:
        affected_rows = upsert_rows(connection, rows, args.batch_size)

    print(f"Backfill completed: {args.start} -> {args.end or 'today'}")
    print("Requested tickers: ^VIX, ^VVIX")
    print(f"Downloaded rows: {len(rows)}")
    print(f"Affected rows: {affected_rows}")


if __name__ == "__main__":
    main()
