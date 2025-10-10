"""CSV loading and caching helpers for analytics data."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Final

import pandas as pd


_DEFAULT_CSV: Final[Path] = (
    Path(__file__).resolve().parent.parent / "data" / "fixtures" / "seed.csv"
)


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalised = value.strip().lower()
        if normalised in {"true", "t", "1", "yes"}:
            return True
        if normalised in {"false", "f", "0", "no"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return False


def _resolve_path(csv_path: str | Path | None) -> Path:
    if csv_path is None:
        return _DEFAULT_CSV
    candidate = Path(csv_path)
    if candidate.is_dir():
        raise ValueError("CSV path must point to a file, not a directory")
    return candidate


def _count_preamble_rows(path: Path) -> int:
    """Determine how many leading rows should be skipped.

    Some fixture exports include an extra header line and a sample row before the
    actual dataset header. We detect those and skip them defensively.
    """

    skip = 0
    with path.open("r", encoding="utf-8") as handle:
        first_line = handle.readline()
        if first_line.startswith("date,description,amount"):
            skip += 1
            second_line = handle.readline()
            if second_line and not second_line.startswith("txn_id"):
                skip += 1
    return skip


@lru_cache(maxsize=4)
def load_transactions(csv_path: str | Path | None = None) -> pd.DataFrame:
    """Load transactions from the fixture CSV and normalise basic columns.

    The first line of the CSV contains demo text and is skipped. Dates are parsed
    to :class:`datetime.date` values and the ``amount`` column is coerced to
    numeric values. Refunds are preserved but flagged for downstream logic.
    """

    path = _resolve_path(csv_path)
    if not path.exists():  # pragma: no cover - defensive guard for bad config
        raise FileNotFoundError(f"Transaction CSV not found: {path}")

    skiprows = _count_preamble_rows(path)
    df = pd.read_csv(path, skiprows=skiprows)

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df = df.dropna(subset=["date"])

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["amount"])

    df["is_refund"] = df["is_refund"].map(_coerce_bool)

    standardised_columns = {"description": "merchant"}
    df = df.rename(columns=standardised_columns)

    # Deduplicate on transaction id when present.
    if "txn_id" in df.columns:
        df = df.sort_values("date").drop_duplicates(subset="txn_id", keep="last")

    ordered_columns = [
        column
        for column in (
            "txn_id",
            "date",
            "amount",
            "currency",
            "merchant",
            "mcc",
            "category",
            "channel",
            "merchant_city",
            "merchant_country",
            "card_last4",
            "is_refund",
            "note",
        )
        if column in df.columns
    ]

    df = df[ordered_columns]
    df = df.sort_values("date").reset_index(drop=True)

    return df


__all__ = ["load_transactions"]
