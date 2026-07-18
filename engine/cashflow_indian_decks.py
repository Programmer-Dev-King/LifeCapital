"""
Indian Rat Race Game — Expanded Card Decks
Features 50+ Indian-specific financial scenarios and opportunities
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List
from enum import Enum

from .cashflow import DealCard, DoodadCard, MarketCard, AssetType


@dataclass
class IndianCardDecks:
    """Complete card deck library with Indian financial products and events."""

    @staticmethod
    def small_deals() -> List[DealCard]:
        return [
            # Stocks & ETFs
            DealCard(
                name="Nifty 50 SIP",
                asset_type=AssetType.STOCK,
                cost=6000.0,
                down_payment=6000.0,
                monthly_cashflow=150.0,
                interest_rate=0.0,
                loan_months=0,
                description="Systematic Investment Plan in India's top 50 companies.",
            ),
            DealCard(
                name="Midcap Fund SIP",
                asset_type=AssetType.STOCK,
                cost=5000.0,
                down_payment=5000.0,
                monthly_cashflow=140.0,
                interest_rate=0.0,
                loan_months=0,
                description="Emerging midcap companies with growth potential.",
            ),
            DealCard(
                name="Dividend Aristocrats",
                asset_type=AssetType.STOCK,
                cost=8000.0,
                down_payment=8000.0,
                monthly_cashflow=200.0,
                interest_rate=0.0,
                loan_months=0,
                description="Blue-chip stocks with reliable dividend income.",
            ),
            # Government Schemes
            DealCard(
                name="Public Provident Fund (PPF)",
                asset_type=AssetType.CD,
                cost=5000.0,
                down_payment=5000.0,
                monthly_cashflow=125.0,
                interest_rate=0.0,
                loan_months=0,
                description="Government-backed long-term savings scheme, 7.1% interest.",
            ),
            DealCard(
                name="Senior Citizen Savings Scheme",
                asset_type=AssetType.CD,
                cost=7000.0,
                down_payment=7000.0,
                monthly_cashflow=210.0,
                interest_rate=0.0,
                loan_months=0,
                description="High-interest scheme for senior citizens, 8.2% p.a.",
            ),
            DealCard(
                name="Sukanya Samriddhi Account",
                asset_type=AssetType.CD,
                cost=6000.0,
                down_payment=6000.0,
                monthly_cashflow=140.0,
                interest_rate=0.0,
                loan_months=0,
                description="Long-term savings for girl child, 8.2% interest.",
            ),
            # Small Business
            DealCard(
                name="Tea Stall Franchise",
                asset_type=AssetType.BUSINESS,
                cost=5000.0,
                down_payment=2000.0,
                monthly_cashflow=400.0,
                interest_rate=0.12,
                loan_months=24,
                description="Quick-commerce tea and snacks outlet.",
            ),
            DealCard(
                name="Coaching Center Franchise",
                asset_type=AssetType.BUSINESS,
                cost=8000.0,
                down_payment=3000.0,
                monthly_cashflow=600.0,
                interest_rate=0.12,
                loan_months=36,
                description="Educational tutoring and skill development center.",
            ),
            DealCard(
                name="Small Shop Kiosk",
                asset_type=AssetType.BUSINESS,
                cost=6500.0,
                down_payment=2500.0,
                monthly_cashflow=500.0,
                interest_rate=0.11,
                loan_months=30,
                description="Retail kiosk in high-traffic area.",
            ),
            DealCard(
                name="Chit Fund Scheme",
                asset_type=AssetType.CD,
                cost=4500.0,
                down_payment=4500.0,
                monthly_cashflow=110.0,
                interest_rate=0.0,
                loan_months=0,
                description="Collective savings group with guaranteed payout.",
            ),
            # Bonds & Fixed Income
            DealCard(
                name="Corporate Bonds",
                asset_type=AssetType.CD,
                cost=7500.0,
                down_payment=7500.0,
                monthly_cashflow=187.0,
                interest_rate=0.0,
                loan_months=0,
                description="Fixed income from rated companies, 7% coupon.",
            ),
            DealCard(
                name="Sovereign Gold Bond",
                asset_type=AssetType.GOLD,
                cost=5000.0,
                down_payment=5000.0,
                monthly_cashflow=100.0,
                interest_rate=0.0,
                loan_months=0,
                description="Gold ownership with government backing, 2.5% interest.",
            ),
        ]

    @staticmethod
    def big_deals() -> List[DealCard]:
        return [
            # Real Estate
            DealCard(
                name="DDA Flat (Delhi)",
                asset_type=AssetType.REAL_ESTATE,
                cost=85000.0,
                down_payment=25000.0,
                monthly_cashflow=3200.0,
                interest_rate=0.09,
                loan_months=180,
                description="Government-allotted residential apartment.",
            ),
            DealCard(
                name="Builder Floor Commercial Space",
                asset_type=AssetType.REAL_ESTATE,
                cost=120000.0,
                down_payment=35000.0,
                monthly_cashflow=4500.0,
                interest_rate=0.09,
                loan_months=180,
                description="Premium commercial property with high rental demand.",
            ),
            DealCard(
                name="Gated Society Apartment (Gurgaon)",
                asset_type=AssetType.REAL_ESTATE,
                cost=100000.0,
                down_payment=30000.0,
                monthly_cashflow=4200.0,
                interest_rate=0.08,
                loan_months=180,
                description="Modern residential complex with amenities.",
            ),
            DealCard(
                name="Retail Shop (Mall)",
                asset_type=AssetType.REAL_ESTATE,
                cost=95000.0,
                down_payment=28000.0,
                monthly_cashflow=3800.0,
                interest_rate=0.08,
                loan_months=170,
                description="High-traffic retail space in commercial mall.",
            ),
            DealCard(
                name="Warehouse Space (Industrial Park)",
                asset_type=AssetType.REAL_ESTATE,
                cost=110000.0,
                down_payment=32000.0,
                monthly_cashflow=4800.0,
                interest_rate=0.09,
                loan_months=180,
                description="Industrial property with long-term lease.",
            ),
            # Businesses
            DealCard(
                name="Organic Farm (Tamil Nadu)",
                asset_type=AssetType.AGRICULTURE,
                cost=90000.0,
                down_payment=25000.0,
                monthly_cashflow=3200.0,
                interest_rate=0.10,
                loan_months=120,
                description="Export-quality organic produce business.",
            ),
            DealCard(
                name="Dairy Farm (Karnataka)",
                asset_type=AssetType.AGRICULTURE,
                cost=85000.0,
                down_payment=24000.0,
                monthly_cashflow=3100.0,
                interest_rate=0.10,
                loan_months=120,
                description="Milk production with cooperative support.",
            ),
            DealCard(
                name="Tech Startup Franchise",
                asset_type=AssetType.BUSINESS,
                cost=150000.0,
                down_payment=45000.0,
                monthly_cashflow=6200.0,
                interest_rate=0.11,
                loan_months=120,
                description="High-return digital services franchise.",
            ),
            DealCard(
                name="Hotel & Restaurant Chain",
                asset_type=AssetType.BUSINESS,
                cost=140000.0,
                down_payment=42000.0,
                monthly_cashflow=5800.0,
                interest_rate=0.12,
                loan_months=120,
                description="Quick-service restaurant with brand recognition.",
            ),
            DealCard(
                name="Fitness Center Franchise",
                asset_type=AssetType.BUSINESS,
                cost=120000.0,
                down_payment=36000.0,
                monthly_cashflow=5000.0,
                interest_rate=0.11,
                loan_months=120,
                description="Modern gym with 300+ members capacity.",
            ),
            DealCard(
                name="Education Center Chain",
                asset_type=AssetType.BUSINESS,
                cost=130000.0,
                down_payment=39000.0,
                monthly_cashflow=5500.0,
                interest_rate=0.11,
                loan_months=120,
                description="Multi-branch coaching and skill center.",
            ),
            DealCard(
                name="Logistics & E-commerce Hub",
                asset_type=AssetType.BUSINESS,
                cost=160000.0,
                down_payment=48000.0,
                monthly_cashflow=6800.0,
                interest_rate=0.12,
                loan_months=120,
                description="Last-mile delivery and warehousing partner.",
            ),
        ]

    @staticmethod
    def doodads() -> List[DoodadCard]:
        return [
            # One-time expenses
            DoodadCard(description="Diwali shopping festival", cost=15000.0, payment_type="one_time"),
            DoodadCard(description="Wedding expenses (cousin)", cost=35000.0, payment_type="one_time"),
            DoodadCard(description="Medical emergency (surgery)", cost=50000.0, payment_type="one_time"),
            DoodadCard(description="Home renovation", cost=20000.0, payment_type="one_time"),
            DoodadCard(description="Vehicle repair (major)", cost=12000.0, payment_type="one_time"),
            DoodadCard(description="Gadget purchase spree", cost=18000.0, payment_type="one_time"),
            DoodadCard(description="Travel & vacation plan", cost=25000.0, payment_type="one_time"),
            DoodadCard(description="Flood/disaster relief donation", cost=8000.0, payment_type="one_time"),
            DoodadCard(description="Laptop replacement", cost=55000.0, payment_type="one_time"),
            DoodadCard(description="Family health checkup", cost=7000.0, payment_type="one_time"),
            # Monthly recurring increases
            DoodadCard(
                description="School fees increase",
                cost=2500.0,
                payment_type="monthly_increase",
                monthly_increase=2500.0,
            ),
            DoodadCard(
                description="House rent hike",
                cost=3000.0,
                payment_type="monthly_increase",
                monthly_increase=3000.0,
            ),
            DoodadCard(
                description="Tuition & coaching fees",
                cost=1800.0,
                payment_type="monthly_increase",
                monthly_increase=1800.0,
            ),
            DoodadCard(
                description="EMI on personal loan",
                cost=4000.0,
                payment_type="monthly_increase",
                monthly_increase=4000.0,
            ),
            DoodadCard(
                description="Insurance premiums increase",
                cost=1200.0,
                payment_type="monthly_increase",
                monthly_increase=1200.0,
            ),
        ]

    @staticmethod
    def markets() -> List[MarketCard]:
        return [
            # Positive market events
            MarketCard(description="Sensex surge: stock values +20%", affects="stock", multiplier=1.20),
            MarketCard(description="Gold rally: commodity boom", affects="gold", multiplier=1.25),
            MarketCard(description="FD maturity payout", affects="cd", multiplier=1.10),
            MarketCard(description="Real estate boom in metros", affects="real_estate", multiplier=1.18),
            MarketCard(description="Agricultural exports surge", affects="agriculture", multiplier=1.22),
            MarketCard(description="Business profits surge", affects="business", multiplier=1.15),
            MarketCard(
                description="GST reduction helps businesses",
                affects="business",
                multiplier=1.12,
                sell_opportunity=True,
            ),
            MarketCard(description="Property prices spike", affects="real_estate", multiplier=1.20, sell_opportunity=True),
            MarketCard(description="Stock split bonus announcement", affects="stock", multiplier=1.08),
            # Negative market events
            MarketCard(description="Stock market crash -15%", affects="stock", multiplier=0.85),
            MarketCard(description="Real estate correction", affects="real_estate", multiplier=0.88),
            MarketCard(description="Gold price dips", affects="gold", multiplier=0.92),
            MarketCard(description="Agricultural prices collapse", affects="agriculture", multiplier=0.75),
            MarketCard(description="Recession hits business sector", affects="business", multiplier=0.82),
            MarketCard(description="Interest rate hike pressures CD", affects="cd", multiplier=1.02),
            MarketCard(description="Currency depreciation affects exports", affects="agriculture", multiplier=0.90),
            MarketCard(description="Property bubble deflates", affects="real_estate", multiplier=0.85),
            # Neutral/mixed
            MarketCard(description="Market consolidation—no major change", affects="stock", multiplier=1.01),
            MarketCard(description="Interest rate steady", affects="cd", multiplier=1.00),
            MarketCard(description="Real estate market stabilizes", affects="real_estate", multiplier=1.03),
        ]


def get_indian_small_deals() -> List[DealCard]:
    """Get all small deal cards for Indian context."""
    return IndianCardDecks.small_deals()


def get_indian_big_deals() -> List[DealCard]:
    """Get all big deal cards for Indian context."""
    return IndianCardDecks.big_deals()


def get_indian_doodads() -> List[DoodadCard]:
    """Get all doodad cards for Indian context."""
    return IndianCardDecks.doodads()


def get_indian_markets() -> List[MarketCard]:
    """Get all market cards for Indian context."""
    return IndianCardDecks.markets()
