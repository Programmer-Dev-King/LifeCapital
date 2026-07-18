from __future__ import annotations

from dataclasses import dataclass
from .player import Player
from .economy import EconomyState


class AIManager:
    """Very small rule-based AI to automate prototype runs."""

    def decide(self, player: Player, econ: EconomyState) -> dict:
        # If cash is high relative to expenses, invest in index
        if player.cash > max(50_000.0, player.expenses * 3):
            amt = player.cash * 0.5
            return {"type": "invest_market", "symbol": "NIFTY_IND", "amount": amt}
        # If net worth is growing slowly and we have cash, buy rental
        if player.cash > 120_000.0:
            return {"type": "buy_rental", "amount": 100_000.0}
        # If negative cashflow and low liquidity, take a loan (risky)
        if player.monthly_cashflow() < 0 and player.cash < player.expenses:
            return {"type": "take_loan", "amount": 100_000.0}
        return {"type": "pass"}
