from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable
import time
import sys

import pandas as pd
import pymysql
import yfinance as yf

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings

DEFAULT_TICKERS = [
    "SPY",
    "QQQ",
    "BRK-B",
    "AAPL",
    "MSFT",
    "AMZN",
    "GOOGL",
    "META",
    "NVDA",
    "TSLA",
]

ASSET_TYPE_MAP = {
    "SPY": "ETF",
    "QQQ": "ETF",
}


@dataclass(frozen=True)
class PriceRow:
    ticker: str
    trade_date: date
    adj_close_price: float


@dataclass(frozen=True)
class SyncResult:
    requested_tickers: list[str]
    success_tickers: list[str]
    failed_tickers: list[str]
    downloaded_rows: int
    affected_rows: int


def parse_tickers(raw_tickers: str | None) -> list[str]:
    if not raw_tickers:
        return list(DEFAULT_TICKERS)
    return [ticker.strip().upper() for ticker in raw_tickers.split(",") if ticker.strip()]


def compute_sync_start(lookback_days: int) -> str:
    return (datetime.utcnow().date() - timedelta(days=lookback_days)).isoformat()


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
    return float(value)


def download_ticker_history(
    ticker: str,
    start: str,
    end: str | None,
) -> list[PriceRow]:
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
        return []

    if isinstance(frame.columns, pd.MultiIndex):
        frame = frame.droplevel("Ticker", axis=1)

    prepared = frame.reset_index().copy()
    prepared.columns = [str(column) for column in prepared.columns]
    if "Date" not in prepared.columns or "Adj Close" not in prepared.columns:
        raise RuntimeError(f"Unexpected Yahoo Finance columns for {ticker}.")

    rows: list[PriceRow] = []
    for _, item in prepared.iterrows():
        adj_close_price = normalize_number(item.get("Adj Close"))
        if adj_close_price is None:
            continue
        rows.append(
            PriceRow(
                ticker=ticker,
                trade_date=pd.Timestamp(item["Date"]).date(),
                adj_close_price=adj_close_price,
            )
        )
    return rows


def download_ticker_history_with_retry(
    ticker: str,
    start: str,
    end: str | None,
    max_attempts: int = 2,
) -> list[PriceRow]:
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return download_ticker_history(ticker=ticker, start=start, end=end)
        except Exception as exc:
            last_error = exc
            if attempt < max_attempts:
                time.sleep(2)
    if last_error is not None:
        raise last_error
    return []


def chunked(values: list[tuple], size: int) -> Iterable[list[tuple]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


def ensure_instruments(
    connection: pymysql.connections.Connection,
    tickers: list[str],
) -> dict[str, int]:
    sql = """
        INSERT INTO dim_instrument (
            ticker,
            asset_type,
            currency_code,
            is_active
        )
        VALUES (%s, %s, 'USD', 1)
        ON DUPLICATE KEY UPDATE
            asset_type = VALUES(asset_type),
            currency_code = VALUES(currency_code),
            is_active = VALUES(is_active)
    """
    with connection.cursor() as cursor:
        cursor.executemany(
            sql,
            [(ticker, ASSET_TYPE_MAP.get(ticker, "EQUITY")) for ticker in tickers],
        )
        placeholders = ",".join(["%s"] * len(tickers))
        cursor.execute(
            f"""
            SELECT instrument_id, ticker
            FROM dim_instrument
            WHERE ticker IN ({placeholders})
            """,
            tickers,
        )
        rows = cursor.fetchall()
    return {ticker: instrument_id for instrument_id, ticker in rows}


def upsert_prices(
    connection: pymysql.connections.Connection,
    instrument_map: dict[str, int],
    rows: list[PriceRow],
    batch_size: int,
) -> int:
    if not rows:
        return 0

    sql_prefix = """
        INSERT INTO raw_equity_daily_price (
            instrument_id,
            trade_date,
            adj_close_price,
            source_system,
            source_ticker
        )
        VALUES
    """
    sql_suffix = """
        ON DUPLICATE KEY UPDATE
            adj_close_price = VALUES(adj_close_price),
            source_system = VALUES(source_system),
            source_ticker = VALUES(source_ticker)
    """
    payload = [
        (
            instrument_map[row.ticker],
            row.trade_date,
            row.adj_close_price,
            row.ticker,
        )
        for row in rows
    ]

    affected_rows = 0
    with connection.cursor() as cursor:
        for batch in chunked(payload, batch_size):
            placeholders = ", ".join(["(%s, %s, %s, 'yfinance', %s)"] * len(batch))
            flat_params: list[object] = []
            for row in batch:
                flat_params.extend(row)
            cursor.execute(sql_prefix + placeholders + sql_suffix, tuple(flat_params))
            affected_rows += cursor.rowcount
    return affected_rows


def sync_prices(
    tickers: list[str],
    start: str,
    end: str | None,
    batch_size: int,
) -> SyncResult:
    success_tickers: list[str] = []
    failed_tickers: list[str] = []
    downloaded_rows = 0
    all_rows: list[PriceRow] = []

    for ticker in tickers:
        try:
            rows = download_ticker_history_with_retry(ticker=ticker, start=start, end=end)
        except Exception:
            failed_tickers.append(ticker)
            continue

        success_tickers.append(ticker)
        downloaded_rows += len(rows)
        all_rows.extend(rows)

    if not success_tickers:
        return SyncResult(
            requested_tickers=tickers,
            success_tickers=[],
            failed_tickers=failed_tickers,
            downloaded_rows=0,
            affected_rows=0,
        )

    with get_connection() as connection:
        instrument_map = ensure_instruments(connection, success_tickers)
        affected_rows = upsert_prices(
            connection=connection,
            instrument_map=instrument_map,
            rows=all_rows,
            batch_size=batch_size,
        )

    return SyncResult(
        requested_tickers=tickers,
        success_tickers=success_tickers,
        failed_tickers=failed_tickers,
        downloaded_rows=downloaded_rows,
        affected_rows=affected_rows,
    )


def print_result(result: SyncResult, label: str, start: str, end: str | None) -> None:
    end_display = end or "today"
    print(f"{label}: {start} -> {end_display}")
    print(f"Requested tickers: {', '.join(result.requested_tickers)}")
    print(f"Successful tickers: {', '.join(result.success_tickers) if result.success_tickers else 'none'}")
    print(f"Failed tickers: {', '.join(result.failed_tickers) if result.failed_tickers else 'none'}")
    print(f"Downloaded rows: {result.downloaded_rows}")
    print(f"Affected rows: {result.affected_rows}")
