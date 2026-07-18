from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict
from .assets import Asset, Liability


@dataclass
class Player:
    name: str
    cash: float
    monthly_income: float
    passive_income: float
    expenses: float
    credit_score: int
    risk_appetite: float  # 0..1
    reputation: float
    region: str = "tier2"
    education: str = "graduate"
    age: int = 25
    dependents: int = 0
    skills: Dict[str, float] = field(default_factory=dict)
    assets: List[Asset] = field(default_factory=list)
    liabilities: List[Liability] = field(default_factory=list)

    def net_worth(self) -> float:
        assets_value = sum(a.value for a in self.assets)
        liabilities_value = sum(l.principal for l in self.liabilities)
        return self.cash + assets_value - liabilities_value

    def monthly_cashflow(self) -> float:
        asset_cash = sum(a.monthly_cashflow for a in self.assets)
        liability_payments = sum(l.monthly_payment for l in self.liabilities)
        return self.monthly_income + self.passive_income + asset_cash - self.expenses - liability_payments

    def apply_month(self) -> None:
        # Collect income
        inflow = self.monthly_income + self.passive_income + sum(a.monthly_cashflow for a in self.assets)
        # Pay liabilities monthly payments
        outflow = self.expenses
        for l in list(self.liabilities):
            pay = l.pay_month()
            outflow += pay
            if l.is_paid_off():
                self.liabilities.remove(l)
        net = inflow - outflow
        self.cash += net

    def add_asset(self, asset: Asset) -> None:
        self.assets.append(asset)

    def add_liability(self, liability: Liability) -> None:
        self.liabilities.append(liability)

    def __str__(self) -> str:
        return (
            f"Player {self.name}: Cash ₹{self.cash:,.0f}, Income ₹{self.monthly_income:,.0f}/mo, "
            f"Passive ₹{self.passive_income:,.0f}/mo, Net Worth ₹{self.net_worth():,.0f}"
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "cash": self.cash,
            "monthly_income": self.monthly_income,
            "passive_income": self.passive_income,
            "expenses": self.expenses,
            "credit_score": self.credit_score,
            "risk_appetite": self.risk_appetite,
            "reputation": self.reputation,
            "region": self.region,
            "education": self.education,
            "age": self.age,
            "dependents": self.dependents,
            "skills": self.skills,
            "assets": [a.to_dict() for a in self.assets],
            "liabilities": [l.to_dict() for l in self.liabilities],
        }

    @staticmethod
    def from_dict(d: dict) -> "Player":
        p = Player(
            name=d.get("name", "Player"),
            cash=d.get("cash", 0.0),
            monthly_income=d.get("monthly_income", 0.0),
            passive_income=d.get("passive_income", 0.0),
            expenses=d.get("expenses", 0.0),
            credit_score=int(d.get("credit_score", 600)),
            risk_appetite=float(d.get("risk_appetite", 0.5)),
            reputation=float(d.get("reputation", 0.5)),
            region=d.get("region", "tier2"),
            education=d.get("education", "graduate"),
            age=int(d.get("age", 25)),
            dependents=int(d.get("dependents", 0)),
            skills=d.get("skills", {}),
        )
        # rebuild assets/liabilities
        for a in d.get("assets", []):
            try:
                p.assets.append(Asset.from_dict(a))
            except Exception:
                pass
        for l in d.get("liabilities", []):
            try:
                p.liabilities.append(Liability.from_dict(l))
            except Exception:
                pass
        return p
