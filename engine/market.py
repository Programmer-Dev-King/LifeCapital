from __future__ import annotations

import random
from typing import List
from .assets import Asset, AssetType


class MarketManager:
    def __init__(self, seed: int | None = None) -> None:
        self.seed = seed
        if seed is not None:
            random.seed(seed)
        # simple list of available instruments in prototype
        self.stocks = [
            {"symbol": "NIFTY_IND", "name": "Nifty Index Proxy", "type": AssetType.STOCK},
            {"symbol": "RE_URB", "name": "Urban Realty Fund", "type": AssetType.RENTAL},
            {"symbol": "AGR_EXP", "name": "Agri Exports Co", "type": AssetType.AGRICULTURE},
        ]

    def list_marketable(self) -> List[dict]:
        return self.stocks

    def create_asset_from_symbol(self, symbol: str, amount: float) -> Asset:
        info = next((s for s in self.stocks if s["symbol"] == symbol), None)
        if not info:
            # default to ETF-like
            return Asset(name=symbol, asset_type=AssetType.ETF, value=amount, monthly_cashflow=0.0, risk=0.2, growth_bias=0.0)
        t = info["type"]
        # risk mapping
        risk = 0.25 if t == AssetType.STOCK else 0.15 if t == AssetType.ETF else 0.20
        return Asset(name=info["name"], asset_type=t, value=amount, monthly_cashflow=0.0, risk=risk, growth_bias=0.01)
