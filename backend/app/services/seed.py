from app.db.session import SessionLocal
from app.models.series import Series

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
]

def main() -> None:
    db = SessionLocal()
    try:
        existing = {s.id for s in db.query(Series).all()}
        to_add = [Series(**row) for row in SEED_SERIES if row["id"] not in existing]
        if to_add:
            db.add_all(to_add)
            db.commit()
        print(f"Seeded. Total series in DB: {db.query(Series).count()}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
