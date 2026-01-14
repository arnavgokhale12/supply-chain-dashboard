#!/usr/bin/env python3
"""Daily data refresh script for Supply Chain Dashboard.

This script refreshes all data sources:
1. Supply chain indicators (FRED, NY Fed)
2. Market data (yfinance)
3. Regime statistics

Run manually: python scripts/daily_refresh.py
Schedule via cron: 0 6 * * * cd /path/to/project && /path/to/venv/bin/python scripts/daily_refresh.py
"""
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set working directory to project root for relative imports
os.chdir(project_root)


def log(msg: str) -> None:
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")


def refresh_supply_chain_indicators() -> None:
    """Refresh all supply chain indicator data."""
    log("Refreshing supply chain indicators...")

    # GSCPI (NY Fed)
    try:
        from backend.app.services.ingest_gscpi import main as ingest_gscpi
        ingest_gscpi()
        log("  ✓ GSCPI updated")
    except Exception as e:
        log(f"  ✗ GSCPI failed: {e}")

    # Cass Freight Index
    try:
        from backend.app.services.ingest_cass import main as ingest_cass
        ingest_cass()
        log("  ✓ Cass Freight updated")
    except Exception as e:
        log(f"  ✗ Cass Freight failed: {e}")

    # Retail Inventories
    try:
        from backend.app.services.ingest_retailirsa import main as ingest_retail
        ingest_retail()
        log("  ✓ Retail Inventories updated")
    except Exception as e:
        log(f"  ✗ Retail Inventories failed: {e}")

    # Additional FRED indicators
    try:
        from backend.app.services.ingest_fred_indicators import main as ingest_fred
        ingest_fred()
        log("  ✓ FRED indicators updated")
    except Exception as e:
        log(f"  ✗ FRED indicators failed: {e}")

    # Baltic Dry Index (optional - requires Quandl API key)
    try:
        from backend.app.services.ingest_baltic_dry import main as ingest_baltic
        ingest_baltic()
        log("  ✓ Baltic Dry Index updated")
    except Exception as e:
        log(f"  ✗ Baltic Dry Index failed: {e}")


def refresh_market_data() -> None:
    """Refresh market data from yfinance."""
    log("Refreshing market data...")

    try:
        from backend.app.services.ingest_market_data import main as ingest_market
        ingest_market()
        log("  ✓ Market prices updated")
    except Exception as e:
        log(f"  ✗ Market data failed: {e}")


def refresh_regime_statistics() -> None:
    """Recompute regime-conditional return statistics."""
    log("Computing regime statistics...")

    try:
        from backend.app.services.regime_analyzer import main as compute_regime
        compute_regime()
        log("  ✓ Regime statistics updated")
    except Exception as e:
        log(f"  ✗ Regime statistics failed: {e}")


def main() -> None:
    """Run full daily refresh."""
    log("=" * 50)
    log("Starting daily data refresh")
    log("=" * 50)

    start_time = datetime.now()

    # Run all refresh tasks
    refresh_supply_chain_indicators()
    refresh_market_data()
    refresh_regime_statistics()

    elapsed = (datetime.now() - start_time).total_seconds()
    log("=" * 50)
    log(f"Daily refresh completed in {elapsed:.1f} seconds")
    log("=" * 50)


if __name__ == "__main__":
    main()
