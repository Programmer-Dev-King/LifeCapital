from __future__ import annotations

import csv
import os
import random
from typing import Dict, Tuple

# Simplified Indian regional and demographic data for prototype sampling.

REGIONS = {
    "metro": {"name": "Metro City", "income_mul": 1.4, "unemployment": 0.05},
    "tier2": {"name": "Tier-2 City", "income_mul": 1.0, "unemployment": 0.06},
    "rural": {"name": "Rural Area", "income_mul": 0.6, "unemployment": 0.08},
}


EDUCATION_LEVELS = {
    "none": 0.6,
    "school": 0.8,
    "graduate": 1.0,
    "postgrad": 1.3,
    "professional": 1.6,
}


def sample_starting_profile(region: str = "tier2", education: str = "graduate", seed: int | None = None) -> Dict:
    """Return a sampled starting profile tuned to region and education.

    Returns: dict with cash, monthly_income, expenses, dependents, age
    """
    if seed is not None:
        random.seed(seed)
    r = REGIONS.get(region, REGIONS["tier2"])
    e_mul = EDUCATION_LEVELS.get(education, 1.0)

    # Try CSV-driven salary sampling if file exists
    csv_path = None
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        csv_path = os.path.join(base_dir, "data", "region_salaries.csv")
    except Exception:
        csv_path = None

    income = None
    if csv_path and os.path.exists(csv_path):
        # load approximate median if available
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                header = f.readline()
                rows = [line.strip().split(",") for line in f.readlines() if line.strip()]
                # find matching median row
                for rrow in rows:
                    if len(rrow) >= 4 and rrow[0] == region and rrow[1] == education and rrow[2] == "0.5":
                        income = float(rrow[3])
                        break
        except Exception:
            income = None

    if income is None:
        base_income = 20000.0
        income = base_income * r["income_mul"] * e_mul * random.uniform(0.7, 1.4)

    # starting cash depends on family & region
    cash = max(0.0, income * random.uniform(0.3, 2.0))
    expenses = income * random.uniform(0.5, 0.9)
    dependents = random.choice([0, 1, 2, 3])
    age = random.randint(20, 35)
    return {
        "cash": round(cash, 2),
        "monthly_income": round(income, 2),
        "expenses": round(expenses, 2),
        "dependents": dependents,
        "age": age,
        "region": region,
        "education": education,
    }


def _load_gst_slabs() -> list[tuple[float, float, float]]:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    csv_path = os.path.join(base_dir, "data", "gst_slabs.csv")
    slabs = []
    if not os.path.exists(csv_path):
        return slabs
    try:
        with open(csv_path, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                slabs.append((float(row["min_annual"]), float(row["max_annual"]), float(row["rate"])))
    except Exception:
        return []
    return slabs


def income_tax_monthly(monthly_income: float) -> float:
    """Simple progressive annual slabs converted to monthly tax (prototype)."""
    annual = monthly_income * 12.0
    slabs = _load_gst_slabs()
    if not slabs:
        slabs = [(0, 250_000, 0.0), (250_000, 500_000, 0.05), (500_000, 1_000_000, 0.20), (1_000_000, float("inf"), 0.30)]
    tax = 0.0
    remaining = annual
    for min_val, max_val, rate in slabs:
        if remaining <= 0:
            break
        taxable = max(0.0, min(remaining, max_val - min_val))
        tax += taxable * rate
        remaining -= taxable
    tax *= 1.04
    return tax / 12.0


def monsoon_shock_probability(region: str = "tier2") -> float:
    r = REGIONS.get(region, REGIONS["tier2"])
    # rural more sensitive
    base = 0.02
    if region == "rural":
        base = 0.08
    return base


def festival_bonus_chance() -> float:
    # Diwali/Onam/others: chance of employer bonus
    return 0.25


def gst_effect_on_price(gst_rate: float, base_price: float) -> float:
    """Return price after GST applied (simplified)."""
    return base_price * (1.0 + gst_rate)


def _load_subsidy_policies() -> dict[str, float]:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    csv_path = os.path.join(base_dir, "data", "subsidy_policies.csv")
    mapping: dict[str, float] = {}
    if not os.path.exists(csv_path):
        return mapping
    try:
        with open(csv_path, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                sector = row.get("sector", "").strip().lower()
                multiplier = float(row.get("policy_multiplier", 0.0))
                mapping[sector] = multiplier
    except Exception:
        return {}
    return mapping


def subsidy_for_sector(sector: str) -> float:
    """Prototype subsidies: return multiplier to incomes/returns for sectors receiving subsidies."""
    policies = _load_subsidy_policies()
    return policies.get(sector.lower(), 0.0)


def _load_event_modifiers() -> dict:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    csv_path = os.path.join(base_dir, "data", "event_modifiers.csv")
    mapping = {}
    if not os.path.exists(csv_path):
        # default modifiers
        return {
            "gst_change_chance": 0.18,
            "festival_bonus_chance": 0.25,
            "strike_impact": 0.12,
            "startup_boost": 0.12,
        }
    try:
        import csv

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row.get("key")
                val = float(row.get("value", 0))
                if key:
                    mapping[key] = val
    except Exception:
        return {}
    return mapping


_EVENT_MODS = _load_event_modifiers()


def get_event_modifier(key: str, default: float = 0.0) -> float:
    return float(_EVENT_MODS.get(key, default))


def apply_subsidy_to_asset(asset_name: str, base_return: float) -> float:
    # naive sector detection
    name = asset_name.lower()
    if "agri" in name or "farm" in name or "agriculture" in name:
        bonus = subsidy_for_sector("agriculture")
    elif "manufact" in name:
        bonus = subsidy_for_sector("manufacturing")
    elif "startup" in name or "saa" in name:
        bonus = subsidy_for_sector("startups")
    elif "solar" in name or "renew" in name:
        bonus = subsidy_for_sector("renewables")
    else:
        bonus = 0.0
    return base_return * (1.0 + bonus)
