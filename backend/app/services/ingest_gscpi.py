from __future__ import annotations

import io
from datetime import date as date_type

import pandas as pd
import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.observation import Observation

LOCAL_SERIES_ID = "gscpi"
NYFED_URL = "https://www.newyorkfed.org/medialibrary/research/interactives/gscpi/downloads/gscpi_data.csv"


def _best_date_col(df: pd.DataFrame) -> int | None:
    best = None
    best_score = 0.0
    for i in range(df.shape[1]):
        s = pd.to_datetime(df.iloc[:, i], errors="coerce")
        score = s.notna().mean()
        if score > best_score:
            best_score = score
            best = i
    # Require at least 30% of rows parse as dates
    return best if best_score >= 0.30 else None


def _best_value_col(df: pd.DataFrame, date_col: int) -> int | None:
    best = None
    best_score = 0.0
    for i in range(df.shape[1]):
        if i == date_col:
            continue
        s = pd.to_numeric(df.iloc[:, i], errors="coerce")
        score = s.notna().mean()
        if score > best_score:
            best_score = score
            best = i
    # Require at least 30% numeric
    return best if best_score >= 0.30 else None


def _extract_date_value_from_sheet(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    df_raw is headerless (header=None). We:
      - find date-like column
      - find numeric-like column
      - drop junk rows
      - return columns: date (YYYY-MM-DD), value (float)
    """
    # remove completely empty rows/cols
    df = df_raw.dropna(axis=0, how="all").dropna(axis=1, how="all")
    if df.empty or df.shape[1] < 2:
        return pd.DataFrame(columns=["date", "value"])

    date_col = _best_date_col(df)
    if date_col is None:
        return pd.DataFrame(columns=["date", "value"])

    val_col = _best_value_col(df, date_col)
    if val_col is None:
        return pd.DataFrame(columns=["date", "value"])

    d = pd.to_datetime(df.iloc[:, date_col], errors="coerce")
    v = pd.to_numeric(df.iloc[:, val_col], errors="coerce")

    out = pd.DataFrame({"date": d, "value": v}).dropna()
    # Keep plausible time series (remove obvious header rows)
    out = out[(out["date"] >= pd.Timestamp("1990-01-01")) & (out["date"] <= pd.Timestamp.today() + pd.Timedelta(days=7))]
    out = out.sort_values("date")

    if out.empty:
        return pd.DataFrame(columns=["date", "value"])

    out["date"] = out["date"].dt.date.astype(str)
    out["value"] = out["value"].astype(float)
    return out


def upsert_observations(db: Session, series_id: str, df: pd.DataFrame) -> int:
    existing_dates = {
        d for (d,) in db.execute(
            select(Observation.date).where(Observation.series_id == series_id)
        ).all()
    }

    to_add: list[Observation] = []
    for _, row in df.iterrows():
        d = date_type.fromisoformat(row["date"][:10])
        if d in existing_dates:
            continue
        to_add.append(Observation(series_id=series_id, date=d, value=float(row["value"])))

    if to_add:
        db.add_all(to_add)
        db.commit()
    return len(to_add)


def main() -> None:
    r = requests.get(NYFED_URL, timeout=30)
    r.raise_for_status()

    xls_bytes = io.BytesIO(r.content)

    # Read all sheets, headerless
    xls = pd.ExcelFile(xls_bytes)
    best_df = pd.DataFrame(columns=["date", "value"])
    best_len = 0

    for sheet in xls.sheet_names:
        df_raw = pd.read_excel(xls, sheet_name=sheet, header=None)
        extracted = _extract_date_value_from_sheet(df_raw)
        if len(extracted) > best_len:
            best_len = len(extracted)
            best_df = extracted

    if best_df.empty:
        print("ERROR: Could not extract any (date, value) series from the NY Fed XLS.")
        print("Sheet names:", xls.sheet_names)
        # Print a small sample of the first sheet for debugging
        sample = pd.read_excel(xls, sheet_name=xls.sheet_names[0], header=None).head(15)
        print("First sheet sample (15 rows):")
        print(sample.to_string(index=False))
        raise SystemExit(1)

    db = SessionLocal()
    try:
        n = upsert_observations(db, LOCAL_SERIES_ID, best_df)
        total = db.query(Observation).filter(Observation.series_id == LOCAL_SERIES_ID).count()
        print(f"Ingested {n} new observations. Total now: {total}")
        print(f"Extracted rows used: {len(best_df)}")
        print("First 3:", best_df.head(3).to_dict(orient="records"))
        print("Last 3:", best_df.tail(3).to_dict(orient="records"))
    finally:
        db.close()


if __name__ == "__main__":
    main()
