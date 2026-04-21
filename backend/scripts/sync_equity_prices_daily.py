from __future__ import annotations

import argparse

from equity_price_loader import compute_sync_start, parse_tickers, print_result, sync_prices


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync recent daily Adj Close prices from Yahoo Finance into MariaDB.",
    )
    parser.add_argument(
        "--tickers",
        default=None,
        help="Comma-separated tickers. Default: SPY,QQQ and Magnificent 7.",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=10,
        help="Number of calendar days to re-fetch. Default: 10.",
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
        help="Rows per executemany batch.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tickers = parse_tickers(args.tickers)
    start = compute_sync_start(args.lookback_days)
    result = sync_prices(
        tickers=tickers,
        start=start,
        end=args.end,
        batch_size=args.batch_size,
    )
    print_result(result, label="Daily sync completed", start=start, end=args.end)


if __name__ == "__main__":
    main()
