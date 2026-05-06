from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys

import pandas as pd
import pymysql

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings

SYMBOL_MAP = {
    "SPXA20R": ("SP500", "above_20d_pct"),
    "SPXA50R": ("SP500", "above_50d_pct"),
    "SPXA200R": ("SP500", "above_200d_pct"),
    "NDXA20R": ("NDX100", "above_20d_pct"),
    "NDXA50R": ("NDX100", "above_50d_pct"),
    "NDXA200R": ("NDX100", "above_200d_pct"),
}


@dataclass(frozen=True)
class BreadthRow:
    trade_date: object
    index_name: str
    above_20d_pct: float | None
    above_50d_pct: float | None
    above_200d_pct: float | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import StockCharts breadth CSV exports into market_breadth.",
    )
    parser.add_argument(
        "--csv-dir",
        default=str(Path.home() / "Downloads"),
        help="Directory containing downloaded StockCharts CSV files.",
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


def normalize_symbol(raw_name: str) -> str | None:
    uppercase = raw_name.upper()
    for symbol in SYMBOL_MAP:
        if symbol in uppercase.replace("$", ""):
            return symbol
    match = re.search(r"(SPXA20R|SPXA50R|SPXA200R|NDXA20R|NDXA50R|NDXA200R)", uppercase)
    if match:
        return match.group(1)
    return None


def detect_symbol_from_path(path: Path) -> str:
    symbol = normalize_symbol(path.name)
    if symbol:
        return symbol
    raise RuntimeError(f"Could not infer breadth symbol from filename: {path}")


def choose_column(columns: list[str], candidates: list[str]) -> str:
    lowered = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    for column in columns:
        lowered_column = column.lower()
        if any(candidate.lower() in lowered_column for candidate in candidates):
            return column
    raise RuntimeError(f"Could not find any of {candidates} in columns {columns}")


def load_symbol_frame(path: Path) -> tuple[str, pd.DataFrame]:
    symbol = detect_symbol_from_path(path)
    frame = pd.read_csv(path)
    columns = [str(column).strip() for column in frame.columns]
    frame.columns = columns

    date_column = choose_column(columns, ["Date"])
    value_column = choose_column(columns, ["Close", "Last", "Value"])

    prepared = frame[[date_column, value_column]].copy()
    prepared.columns = ["trade_date", "indicator_value"]
    prepared["trade_date"] = pd.to_datetime(prepared["trade_date"], errors="coerce").dt.date
    prepared["indicator_value"] = pd.to_numeric(prepared["indicator_value"], errors="coerce")
    prepared = prepared.dropna(subset=["trade_date", "indicator_value"])
    prepared["indicator_value"] = prepared["indicator_value"].round(2)
    return symbol, prepared


def load_all_frames(csv_dir: Path) -> pd.DataFrame:
    collected: dict[str, pd.DataFrame] = {}
    for path in sorted(csv_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() != ".csv":
            continue
        try:
            symbol, frame = load_symbol_frame(path)
        except RuntimeError:
            continue
        collected[symbol] = frame

    missing_symbols = [symbol for symbol in SYMBOL_MAP if symbol not in collected]
    if missing_symbols:
        raise RuntimeError(f"Missing CSV files for symbols: {', '.join(missing_symbols)}")

    merged_frames: list[pd.DataFrame] = []
    for symbol, frame in collected.items():
        index_name, field_name = SYMBOL_MAP[symbol]
        renamed = frame.rename(columns={"indicator_value": field_name}).copy()
        renamed["index_name"] = index_name
        merged_frames.append(renamed)

    result = pd.concat(merged_frames, ignore_index=True)
    grouped = (
        result.groupby(["trade_date", "index_name"], as_index=False)
        .agg(
            above_20d_pct=("above_20d_pct", "max"),
            above_50d_pct=("above_50d_pct", "max"),
            above_200d_pct=("above_200d_pct", "max"),
        )
        .sort_values(["trade_date", "index_name"])
    )
    return grouped


def chunked(values: list[tuple], size: int) -> list[list[tuple]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


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
            above_20d_pct = VALUES(above_20d_pct),
            above_50d_pct = VALUES(above_50d_pct),
            above_200d_pct = VALUES(above_200d_pct)
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
    csv_dir = Path(args.csv_dir).expanduser().resolve()
    frame = load_all_frames(csv_dir)
    with get_connection() as connection:
        affected_rows = upsert_rows(connection, frame, args.batch_size)

    print(f"CSV directory: {csv_dir}")
    print(f"Loaded rows: {len(frame)}")
    print(f"Affected rows: {affected_rows}")
    print("Symbols: " + ", ".join(SYMBOL_MAP.keys()))


if __name__ == "__main__":
    main()
