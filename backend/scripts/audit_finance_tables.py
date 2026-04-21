from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
import sys

import pymysql

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings


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


def compact_ranges(dates: Iterable) -> list[tuple]:
    ordered = sorted(dates)
    if not ordered:
        return []
    ranges: list[tuple] = []
    start = prev = ordered[0]
    for current in ordered[1:]:
        if (current - prev).days == 1:
            prev = current
            continue
        ranges.append((start, prev))
        start = prev = current
    ranges.append((start, prev))
    return ranges


def print_ranges(label: str, dates: list, limit: int = 20) -> None:
    print(label, len(dates))
    for start, end in compact_ranges(dates)[:limit]:
        print(f"  {start} -> {end}")


def main() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT p.trade_date
                FROM raw_equity_daily_price p
                JOIN dim_instrument i ON i.instrument_id = p.instrument_id
                WHERE i.ticker = 'SPY'
                ORDER BY p.trade_date
                """
            )
            spy_dates = [row[0] for row in cursor.fetchall()]
            spy_set = set(spy_dates)

            print("=== dim_instrument ===")
            cursor.execute(
                """
                SELECT instrument_id, ticker, asset_type, is_active
                FROM dim_instrument
                ORDER BY ticker
                """
            )
            for row in cursor.fetchall():
                print(row)
            print()

            print("=== raw_equity_daily_price ===")
            cursor.execute(
                """
                SELECT i.ticker, COUNT(*), MIN(p.trade_date), MAX(p.trade_date),
                       SUM(CASE WHEN p.adj_close_price IS NULL THEN 1 ELSE 0 END)
                FROM raw_equity_daily_price p
                JOIN dim_instrument i ON i.instrument_id = p.instrument_id
                GROUP BY i.ticker
                ORDER BY i.ticker
                """
            )
            for row in cursor.fetchall():
                print(row)
            print()

            print("=== raw_vix ===")
            cursor.execute(
                """
                SELECT COUNT(*), MIN(trade_date), MAX(trade_date),
                       SUM(CASE WHEN vix_close IS NULL THEN 1 ELSE 0 END),
                       SUM(CASE WHEN vvix_close IS NULL THEN 1 ELSE 0 END)
                FROM raw_vix
                """
            )
            print(cursor.fetchone())
            cursor.execute("SELECT trade_date FROM raw_vix")
            raw_vix_dates = {row[0] for row in cursor.fetchall()}
            missing_vix = [
                trade_date
                for trade_date in spy_dates
                if raw_vix_dates and min(raw_vix_dates) <= trade_date <= max(raw_vix_dates) and trade_date not in raw_vix_dates
            ]
            print_ranges("missing_vix_vs_spy", missing_vix)
            cursor.execute("SELECT trade_date FROM raw_vix WHERE vvix_close IS NOT NULL ORDER BY trade_date")
            vvix_dates = [row[0] for row in cursor.fetchall()]
            vvix_set = set(vvix_dates)
            vvix_missing = [
                trade_date
                for trade_date in spy_dates
                if vvix_dates and vvix_dates[0] <= trade_date <= vvix_dates[-1] and trade_date not in vvix_set
            ]
            print_ranges("missing_vvix_within_non_null_range", vvix_missing)
            print()

            print("=== raw_fng ===")
            cursor.execute(
                """
                SELECT COUNT(*), MIN(trade_date), MAX(trade_date),
                       SUM(CASE WHEN fng_value IS NULL THEN 1 ELSE 0 END)
                FROM raw_fng
                """
            )
            print(cursor.fetchone())
            cursor.execute("SELECT trade_date FROM raw_fng")
            raw_fng_dates = {row[0] for row in cursor.fetchall()}
            missing_fng = [
                trade_date
                for trade_date in spy_dates
                if raw_fng_dates and min(raw_fng_dates) <= trade_date <= max(raw_fng_dates) and trade_date not in raw_fng_dates
            ]
            print_ranges("missing_fng_vs_spy", missing_fng)
            print()

            print("=== market_breadth ===")
            cursor.execute(
                """
                SELECT index_name, COUNT(*), MIN(trade_date), MAX(trade_date),
                       SUM(CASE WHEN above_20d_pct IS NULL THEN 1 ELSE 0 END),
                       SUM(CASE WHEN above_50d_pct IS NULL THEN 1 ELSE 0 END),
                       SUM(CASE WHEN above_200d_pct IS NULL THEN 1 ELSE 0 END)
                FROM market_breadth
                GROUP BY index_name
                ORDER BY index_name
                """
            )
            breadth_rows = cursor.fetchall()
            for row in breadth_rows:
                print(row)
            for index_name, *_ in breadth_rows:
                cursor.execute(
                    """
                    SELECT trade_date FROM market_breadth
                    WHERE index_name = %s
                    ORDER BY trade_date
                    """,
                    (index_name,),
                )
                dates = [row[0] for row in cursor.fetchall()]
                date_set = set(dates)
                missing = [
                    trade_date
                    for trade_date in spy_dates
                    if dates and dates[0] <= trade_date <= dates[-1] and trade_date not in date_set
                ]
                print_ranges(f"missing_{index_name}_vs_spy", missing)
            print()

            print("=== index_valuation ===")
            cursor.execute(
                """
                SELECT index_name, COUNT(*), MIN(trade_date), MAX(trade_date),
                       SUM(CASE WHEN pe_ntm IS NULL THEN 1 ELSE 0 END)
                FROM index_valuation
                GROUP BY index_name
                ORDER BY index_name
                """
            )
            valuation_rows = cursor.fetchall()
            for row in valuation_rows:
                print(row)
            print("checked_series", len(valuation_rows))


if __name__ == "__main__":
    main()
