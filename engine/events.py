from __future__ import annotations

import random
from typing import Tuple
from .economy import EconomyManager
from .player import Player
from . import india_data


class EventManager:
    def __init__(self, seed: int | None = None) -> None:
        if seed is not None:
            random.seed(seed)

    def generate_event(self, econ: EconomyManager, player: Player) -> Tuple[str, dict]:
        r = random.random()
        s = econ.state

        if r < india_data.get_event_modifier("recession_chance", 0.05):
            s.gdp_growth = max(-0.05, s.gdp_growth - 0.02)
            s.market_sentiment *= 0.88
            return ("Macro slowdown: GDP and markets weaken.", {"impact": "recession"})

        if r < india_data.get_event_modifier("festival_chance", 0.12):
            if random.random() < india_data.get_event_modifier("festival_bonus_chance", india_data.festival_bonus_chance()):
                bonus = max(0.0, player.monthly_income * (0.05 + random.random() * 0.25))
                player.cash += bonus
                return (f"Festival Bonus: Received ₹{bonus:,.0f}", {"impact": "bonus", "bonus": bonus})
            return ("Festival season is quiet this month.", {"impact": "none"})

        if r < india_data.get_event_modifier("gst_change_chance", 0.18):
            gst_change = random.choice([-0.015, 0.015, 0.02])
            s.inflation = max(0.01, s.inflation + gst_change)
            return (
                f"GST policy shift: inflation changed by {gst_change:+.1%}.",
                {"impact": "gst_change", "change": gst_change},
            )

        if r < india_data.get_event_modifier("monsoon_chance", 0.26):
            prob = india_data.monsoon_shock_probability(getattr(player, "region", "tier2"))
            if random.random() < prob:
                for a in player.assets:
                    if a.asset_type.value == "Agriculture":
                        a.update_value(0.8)
                return ("Monsoon shock: agricultural returns hit.", {"impact": "monsoon"})
            return ("Rainfall outlook looks stable.", {"impact": "none"})

        if r < 0.34:
            startups = [a for a in player.assets if "Startup" in a.name or "SaaS" in a.name]
            if startups:
                for a in startups:
                    growth = 1.1 + random.random() * 0.15
                    a.update_value(growth)
                return ("Startup funding round: selected ventures gain value.", {"impact": "startup_funding"})
            return ("Startup ecosystem remains steady.", {"impact": "none"})

        if r < 0.42:
            if random.random() < 0.35:
                strike_cost = player.expenses * 0.12
                player.cash -= strike_cost
                return (
                    "Labor unrest: short-term cost from supply-chain disruptions.",
                    {"impact": "strike", "cost": strike_cost},
                )
            rate_change = random.choice([-0.01, 0.01])
            s.interest_rate = max(0.01, s.interest_rate + rate_change)
            return (
                "Central bank decision: interest rate adjusted.",
                {"impact": "rate_decision", "change": rate_change},
            )

        if r < 0.50:
            sector = random.choice(["agriculture", "manufacturing", "startups", "renewables"])
            bonus = india_data.subsidy_for_sector(sector)
            if bonus > 0:
                payout = player.monthly_income * bonus * random.uniform(0.8, 1.2)
                player.cash += payout
                return (
                    f"Government subsidy: ₹{payout:,.0f} payout for {sector} sector.",
                    {"impact": "subsidy_payout", "sector": sector, "amount": payout},
                )
            return ("Subsidy programs are being reviewed this round.", {"impact": "subsidy_none"})

        if r < 0.58:
            promo_chance = max(0.05, 0.25 - s.unemployment_rate)
            if random.random() < promo_chance:
                bonus = player.monthly_income * (0.05 + random.random() * 0.2)
                player.monthly_income += bonus
                return (
                    f"Promotion: Income increased by ₹{bonus:,.0f}/mo.",
                    {"impact": "promotion", "bonus": bonus},
                )
            loss = player.monthly_income * (0.1 + random.random() * 0.3)
            player.monthly_income = max(0.0, player.monthly_income - loss)
            return (
                "Job disruption: income reduced temporarily.",
                {"impact": "layoff", "loss": loss},
            )

        if r < 0.66:
            if random.random() < 0.5:
                s.real_estate_index *= 1.05
                return ("Regional property demand rises.", {"impact": "property_boom"})
            s.real_estate_index *= 0.96
            return ("Property correction in some markets.", {"impact": "property_correction"})

        if r < 0.74:
            tax = india_data.income_tax_monthly(player.monthly_income)
            player.cash -= tax
            return (
                f"Tax withholding: ₹{tax:,.0f} deducted.",
                {"impact": "tax", "amount": tax},
            )

        return ("Routine month", {"impact": "none"})
