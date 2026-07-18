from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class EconomyState:
    month: int = 0
    inflation: float = 0.06  # 6% annual ~ monthly ~0.5%
    interest_rate: float = 0.08  # 8% base
    unemployment_rate: float = 0.06
    real_estate_index: float = 100.0
    stock_index: float = 100.0
    gdp_growth: float = 0.05
    market_sentiment: float = 1.0


class EconomyManager:
    def __init__(self, seed: int | None = None) -> None:
        self.state = EconomyState()
        if seed is not None:
            random.seed(seed)

    def step(self) -> EconomyState:
        s = self.state
        s.month += 1
        # small random walk components
        infl_move = random.gauss(0, 0.002)  # monthly inflation drift
        s.inflation = max(0.01, s.inflation + infl_move)

        ir_move = random.gauss(0, 0.001)
        s.interest_rate = max(0.01, s.interest_rate + ir_move)

        ue_move = random.gauss(0, 0.002)
        s.unemployment_rate = min(max(0.02, s.unemployment_rate + ue_move), 0.25)

        # Indices follow sentiment and inflation
        sentiment = random.uniform(0.98, 1.02)
        s.market_sentiment = sentiment
        s.stock_index *= 1.0 + (s.gdp_growth * 0.5 + (sentiment - 1.0) * 0.4 - s.inflation * 0.1)
        s.real_estate_index *= 1.0 + (s.gdp_growth * 0.4 + (sentiment - 1.0) * 0.3 - s.inflation * 0.05)

        # clamp
        s.stock_index = max(10.0, s.stock_index)
        s.real_estate_index = max(10.0, s.real_estate_index)

        return s

    def asset_multiplier(self, asset_type: str, risk: float) -> float:
        # Provide a monthly multiplier for asset values based on economy and risk
        s = self.state
        base = 1.0
        if asset_type == "Stock":
            base += (s.stock_index / 100.0 - 1.0) * (0.2 + risk * 0.5)
        elif asset_type == "ETF":
            base += (s.stock_index / 100.0 - 1.0) * (0.12 + risk * 0.25)
        elif asset_type == "Rental Property":
            base += (s.real_estate_index / 100.0 - 1.0) * (0.08 + risk * 0.2)
        else:
            base += (s.gdp_growth * 0.5 - s.inflation * 0.2) * (0.5 + risk * 0.5)
        # small random noise
        noise = random.gauss(0, 0.01) * (1.0 + risk)
        return max(0.85, 1.0 + base * 0.01 + noise)
