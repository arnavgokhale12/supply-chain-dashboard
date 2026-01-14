"""Seed database with initial series and indicator configurations."""
from backend.app.db.session import SessionLocal
from backend.app.models.indicator_config import IndicatorConfig
from backend.app.models.market_series import MarketSeries
from backend.app.models.series import Series

SEED_SERIES = [
    {
        "id": "gscpi",
        "name": "Global Supply Chain Pressure Index (NY Fed)",
        "frequency": "monthly",
        "source": "New York Fed",
        "url": "https://www.newyorkfed.org/research/policy/gscpi",
    },
    {
        "id": "gscsi",
        "name": "Global Supply Chain Stress Index (World Bank)",
        "frequency": "monthly",
        "source": "World Bank",
        "url": "https://www.worldbank.org/en/data/interactive/2025/04/08/global-supply-chain-stress-index",
    },
    {
        "id": "fbx",
        "name": "Freightos Baltic Index (FBX)",
        "frequency": "daily/weekly",
        "source": "Freightos",
        "url": "https://terminal.freightos.com/freightos-baltic-index-global-container-pricing-index/",
    },
    {
        "id": "cass",
        "name": "Cass Freight Index (Shipments/Expenditures)",
        "frequency": "monthly",
        "source": "Cass Information Systems",
        "url": "https://www.cassinfo.com/freight-audit-payment/cass-transportation-indexes/cass-freight-index",
    },
    {
        "id": "retailirsa",
        "name": "Retailers' Inventories-to-Sales Ratio (FRED: RETAILIRSA)",
        "frequency": "monthly",
        "source": "FRED",
        "url": "https://fred.stlouisfed.org/series/RETAILIRSA",
    },
    # New indicators
    {
        "id": "baltic_dry",
        "name": "Baltic Dry Index",
        "frequency": "daily",
        "source": "Baltic Exchange via Nasdaq Data Link",
        "url": "https://data.nasdaq.com/data/LLOYDS/BDI",
    },
    {
        "id": "ism_supplier",
        "name": "ISM Supplier Deliveries Index",
        "frequency": "monthly",
        "source": "FRED",
        "url": "https://fred.stlouisfed.org/series/ISMPMI",
    },
    {
        "id": "mfg_new_orders",
        "name": "Manufacturing New Orders",
        "frequency": "monthly",
        "source": "FRED",
        "url": "https://fred.stlouisfed.org/series/NEWORDER",
    },
    {
        "id": "wholesale_ratio",
        "name": "Wholesale Inventories/Sales Ratio",
        "frequency": "monthly",
        "source": "FRED",
        "url": "https://fred.stlouisfed.org/series/ISRATIO",
    },
]

# Indicator configurations for composite calculation
SEED_INDICATOR_CONFIGS = [
    {"series_id": "gscpi", "include_in_composite": True, "weight": 1.0, "invert_sign": False, "display_order": 1},
    {"series_id": "retailirsa", "include_in_composite": True, "weight": 1.0, "invert_sign": False, "display_order": 2},
    {"series_id": "cass", "include_in_composite": True, "weight": 1.0, "invert_sign": False, "display_order": 3},
    {"series_id": "baltic_dry", "include_in_composite": True, "weight": 1.0, "invert_sign": False, "display_order": 4},
    {"series_id": "ism_supplier", "include_in_composite": True, "weight": 1.0, "invert_sign": False, "display_order": 5},
    {"series_id": "mfg_new_orders", "include_in_composite": True, "weight": 1.0, "invert_sign": False, "display_order": 6},
    {"series_id": "wholesale_ratio", "include_in_composite": True, "weight": 1.0, "invert_sign": False, "display_order": 7},
]

# Market series for stocks, ETFs, indices
SEED_MARKET_SERIES = [
    {"symbol": "SPY", "name": "S&P 500 ETF", "series_type": "index", "theme": None},
    {"symbol": "XLI", "name": "Industrial Select Sector SPDR", "series_type": "etf", "theme": "industrials"},
    {"symbol": "XLY", "name": "Consumer Discretionary Select SPDR", "series_type": "etf", "theme": "consumer"},
    {"symbol": "XLK", "name": "Technology Select Sector SPDR", "series_type": "etf", "theme": "technology"},
    {"symbol": "SMH", "name": "VanEck Semiconductor ETF", "series_type": "etf", "theme": "chips"},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "series_type": "stock", "theme": "chips"},
    {"symbol": "TSM", "name": "Taiwan Semiconductor", "series_type": "stock", "theme": "chips"},
    {"symbol": "AVGO", "name": "Broadcom Inc", "series_type": "stock", "theme": "chips"},
    {"symbol": "AMZN", "name": "Amazon.com Inc", "series_type": "stock", "theme": "logistics"},
    {"symbol": "COST", "name": "Costco Wholesale", "series_type": "stock", "theme": "retail"},
    {"symbol": "WMT", "name": "Walmart Inc", "series_type": "stock", "theme": "retail"},
]


def seed_series(db) -> int:
    """Seed series table. Returns count of new records."""
    existing = {s.id for s in db.query(Series).all()}
    to_add = [Series(**row) for row in SEED_SERIES if row["id"] not in existing]
    if to_add:
        db.add_all(to_add)
        db.commit()
    return len(to_add)


def seed_indicator_configs(db) -> int:
    """Seed indicator configs. Returns count of new records."""
    existing = {c.series_id for c in db.query(IndicatorConfig).all()}
    to_add = [
        IndicatorConfig(**row)
        for row in SEED_INDICATOR_CONFIGS
        if row["series_id"] not in existing
    ]
    if to_add:
        db.add_all(to_add)
        db.commit()
    return len(to_add)


def seed_market_series(db) -> int:
    """Seed market series. Returns count of new records."""
    existing = {s.symbol for s in db.query(MarketSeries).all()}
    to_add = [
        MarketSeries(**row)
        for row in SEED_MARKET_SERIES
        if row["symbol"] not in existing
    ]
    if to_add:
        db.add_all(to_add)
        db.commit()
    return len(to_add)


def main() -> None:
    db = SessionLocal()
    try:
        n_series = seed_series(db)
        n_configs = seed_indicator_configs(db)
        n_market = seed_market_series(db)

        print(f"Seeded {n_series} new series (total: {db.query(Series).count()})")
        print(f"Seeded {n_configs} new indicator configs (total: {db.query(IndicatorConfig).count()})")
        print(f"Seeded {n_market} new market series (total: {db.query(MarketSeries).count()})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
