from __future__ import annotations
import requests
from backend.app.core.config import settings

def fetch_fred_series(series_id: str) -> list[tuple[str, float]]:
    if not settings.fred_api_key:
        raise RuntimeError("FRED_API_KEY missing in .env")

    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": settings.fred_api_key,
        "file_type": "json",
        "sort_order": "asc",
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    out: list[tuple[str, float]] = []
    for obs in data.get("observations", []):
        v = obs["value"]
        if v == ".":
            continue
        out.append((obs["date"], float(v)))
    return out
