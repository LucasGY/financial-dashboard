from __future__ import annotations

import argparse

from equity_price_loader import parse_tickers, print_result, sync_prices


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill daily Adj Close prices from Yahoo Finance into MariaDB.",
    )
    parser.add_argument(
        "--tickers",
        default=None,
        help="Comma-separated tickers. Default: SPY,QQQ,BRK-B and Magnificent 7.",
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
        help="Rows per executemany batch.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tickers = parse_tickers(args.tickers)
    result = sync_prices(
        tickers=tickers,
        start=args.start,
        end=args.end,
        batch_size=args.batch_size,
    )
    print_result(result, label="Backfill completed", start=args.start, end=args.end)


if __name__ == "__main__":
    main()
