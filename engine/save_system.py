from __future__ import annotations

import json
from typing import Any
from .player import Player
from .economy import EconomyState


def save_game(path: str, player: Player, economy: EconomyState) -> None:
    payload = {
        "player": player.to_dict(),
        "economy": {
            "month": economy.month,
            "inflation": economy.inflation,
            "interest_rate": economy.interest_rate,
            "unemployment_rate": economy.unemployment_rate,
            "real_estate_index": economy.real_estate_index,
            "stock_index": economy.stock_index,
            "gdp_growth": economy.gdp_growth,
            "market_sentiment": economy.market_sentiment,
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def load_game(path: str) -> tuple[Player, EconomyState] | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        player = Player.from_dict(payload.get("player", {}))
        econ = EconomyState(**payload.get("economy", {}))
        return player, econ
    except FileNotFoundError:
        return None
