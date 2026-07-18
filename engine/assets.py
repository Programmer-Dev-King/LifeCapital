from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AssetType(str, Enum):
    STOCK = "Stock"
    ETF = "ETF"
    RENTAL = "Rental Property"
    BUSINESS = "Business"
    CONTENT = "Content Channel"
    AGRICULTURE = "Agriculture"


class LiabilityType(str, Enum):
    EDUCATION_LOAN = "Education Loan"
    CAR_LOAN = "Car Loan"
    HOME_LOAN = "Home Loan"
    CREDIT_CARD = "Credit Card"
    BUSINESS_LOAN = "Business Debt"


@dataclass
class Asset:
    name: str
    asset_type: AssetType
    value: float
    monthly_cashflow: float
    risk: float
    growth_bias: float

    def update_value(self, multiplier: float) -> None:
        self.value *= multiplier

    def update_cashflow(self, economy_multiplier: float) -> None:
        self.monthly_cashflow *= economy_multiplier

    def __str__(self) -> str:
        return f"{self.name} ({self.asset_type.value}): Value ₹{self.value:,.0f}, Cashflow ₹{self.monthly_cashflow:,.0f}/mo"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "asset_type": self.asset_type.value,
            "value": self.value,
            "monthly_cashflow": self.monthly_cashflow,
            "risk": self.risk,
            "growth_bias": self.growth_bias,
        }

    @staticmethod
    def from_dict(d: dict) -> "Asset":
        return Asset(
            name=d["name"],
            asset_type=AssetType(d["asset_type"]),
            value=d.get("value", 0.0),
            monthly_cashflow=d.get("monthly_cashflow", 0.0),
            risk=d.get("risk", 0.0),
            growth_bias=d.get("growth_bias", 0.0),
        )


@dataclass
class Liability:
    name: str
    liability_type: LiabilityType
    principal: float
    monthly_payment: float
    interest_rate: float
    remaining_months: int

    def pay_month(self) -> float:
        payment = min(self.monthly_payment, self.principal)
        self.principal -= payment
        self.remaining_months = max(0, self.remaining_months - 1)
        return payment

    def is_paid_off(self) -> bool:
        return self.principal <= 0 or self.remaining_months <= 0

    def __str__(self) -> str:
        return f"{self.name} ({self.liability_type.value}): Remaining ₹{self.principal:,.0f}, Payment ₹{self.monthly_payment:,.0f}/mo"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "liability_type": self.liability_type.value,
            "principal": self.principal,
            "monthly_payment": self.monthly_payment,
            "interest_rate": self.interest_rate,
            "remaining_months": self.remaining_months,
        }

    @staticmethod
    def from_dict(d: dict) -> "Liability":
        return Liability(
            name=d["name"],
            liability_type=LiabilityType(d["liability_type"]),
            principal=d.get("principal", 0.0),
            monthly_payment=d.get("monthly_payment", 0.0),
            interest_rate=d.get("interest_rate", 0.0),
            remaining_months=int(d.get("remaining_months", 0)),
        )
