from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict

from .india_data import income_tax_monthly


class AssetType(str, Enum):
    REAL_ESTATE = "real_estate"
    STOCK = "stock"
    BUSINESS = "business"
    GOLD = "gold"
    CD = "cd"
    AGRICULTURE = "agriculture"
    OTHER = "other"


class LiabilityType(str, Enum):
    MORTGAGE = "mortgage"
    CAR_LOAN = "car_loan"
    BANK_LOAN = "bank_loan"


@dataclass
class Asset:
    name: str
    asset_type: AssetType
    value: float
    cashflow: float
    purchase_price: float
    down_payment: float = 0.0
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "asset_type": self.asset_type.value,
            "value": self.value,
            "cashflow": self.cashflow,
            "purchase_price": self.purchase_price,
            "down_payment": self.down_payment,
            "notes": self.notes,
        }


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
        self.principal = max(0.0, self.principal - payment)
        self.remaining_months = max(0, self.remaining_months - 1)
        return payment

    def is_paid_off(self) -> bool:
        return self.principal <= 0.0 or self.remaining_months <= 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "liability_type": self.liability_type.value,
            "principal": self.principal,
            "monthly_payment": self.monthly_payment,
            "interest_rate": self.interest_rate,
            "remaining_months": self.remaining_months,
        }


@dataclass
class Player:
    name: str
    profession: str
    region: str
    salary: float
    taxes: float
    other_expenses: float
    children: int
    child_cost_per_month: float
    cash: float
    position: int = 0
    ft_position: int = 0
    on_fast_track: bool = False
    ft_monthly_income: float = 0.0
    owns_dream: bool = False
    dream_cost: float = 0.0
    bankrupt: bool = False
    skip_turns: int = 0
    assets: List[Asset] = field(default_factory=list)
    liabilities: List[Liability] = field(default_factory=list)

    def passive_income(self) -> float:
        return sum(asset.cashflow for asset in self.assets if asset.cashflow > 0)

    def total_income(self) -> float:
        return self.salary + self.passive_income()

    def loan_payments(self) -> float:
        return sum(li.monthly_payment for li in self.liabilities if not li.is_paid_off())

    def total_expenses(self) -> float:
        child_costs = self.children * self.child_cost_per_month
        return self.taxes + self.other_expenses + child_costs + self.loan_payments()

    def monthly_cashflow(self) -> float:
        return self.total_income() - self.total_expenses()

    def net_worth(self) -> float:
        asset_value = sum(a.value for a in self.assets)
        liability_value = sum(l.principal for l in self.liabilities)
        return self.cash + asset_value - liability_value

    def recalculate(self) -> None:
        self.taxes = income_tax_monthly(self.salary)
        if self.children < 0:
            self.children = 0
        self.child_cost_per_month = max(self.child_cost_per_month, 0.0)

    def apply_payday(self) -> str:
        self.recalculate()
        cashflow = self.monthly_cashflow()
        self.cash += cashflow
        if cashflow >= 0:
            return f"PAYDAY: Received ₹{cashflow:,.0f}."
        if self.cash < 0:
            if self.sell_assets_to_cover():
                return f"PAYDAY: Cashflow negative and sold assets to cover shortfall."  # type: ignore
            self.bankrupt = True
            return "PAYDAY: Negative cashflow led to bankruptcy."
        return f"PAYDAY: Paid negative cashflow ₹{abs(cashflow):,.0f}."

    def sell_assets_to_cover(self) -> bool:
        if self.cash >= 0:
            return True
        sortable_assets = sorted(self.assets, key=lambda a: a.value, reverse=True)
        while sortable_assets and self.cash < 0:
            asset = sortable_assets.pop(0)
            self.assets.remove(asset)
            self.cash += asset.value * 0.9
        return self.cash >= 0

    def add_asset(self, asset: Asset) -> None:
        self.assets.append(asset)

    def add_liability(self, liability: Liability) -> None:
        self.liabilities.append(liability)

    def pay_liabilities(self) -> float:
        paid = 0.0
        for liability in list(self.liabilities):
            if liability.is_paid_off():
                self.liabilities.remove(liability)
                continue
            paid += liability.pay_month()
            if liability.is_paid_off():
                self.liabilities.remove(liability)
        return paid

    def check_escape(self) -> bool:
        return self.passive_income() > self.total_expenses()


@dataclass
class DealCard:
    name: str
    asset_type: AssetType
    cost: float
    down_payment: float
    monthly_cashflow: float
    interest_rate: float
    loan_months: int
    description: str
    notes: str = ""


@dataclass
class DoodadCard:
    description: str
    cost: float
    payment_type: str
    monthly_increase: float = 0.0


@dataclass
class MarketCard:
    description: str
    affects: str
    multiplier: float
    sell_opportunity: bool = False


@dataclass
class BoardSpace:
    name: str
    space_type: str
    description: str = ""
    deck_name: Optional[str] = None


RAT_RACE_BOARD: List[BoardSpace] = [
    BoardSpace("Payday", "PAYDAY", "Collect your monthly cashflow."),
    BoardSpace("Small Deal", "SMALL_DEAL", "Opportunity card with small down payment."),
    BoardSpace("Doodad", "DOODAD", "Unexpected expense hits."),
    BoardSpace("Market", "MARKET", "Market forces change asset values."),
    BoardSpace("Baby", "BABY", "Welcome a new child and increased expenses."),
    BoardSpace("Big Deal", "BIG_DEAL", "Opportunity card with larger investment."),
    BoardSpace("Payday", "PAYDAY", "Collect your monthly cashflow."),
    BoardSpace("Charity", "CHARITY", "Donate a portion of your cash for social good."),
    BoardSpace("Small Deal", "SMALL_DEAL", "Small opportunity in Indian markets."),
    BoardSpace("Downsized", "DOWNSIZED", "Job loss forces a difficult turn."),
    BoardSpace("Market", "MARKET", "Market news affects asset values."),
    BoardSpace("Big Deal", "BIG_DEAL", "Bigger investment opportunity arrives."),
    BoardSpace("Doodad", "DOODAD", "A mandatory spending event occurs."),
    BoardSpace("Payday", "PAYDAY", "Collect your monthly cashflow."),
    BoardSpace("Big Deal", "BIG_DEAL", "High-value opportunity on the board."),
    BoardSpace("Market", "MARKET", "Market swings change value."),
]

FAST_TRACK_BOARD: List[BoardSpace] = [
    BoardSpace("Cashflow Day", "CASHFLOW_DAY", "Collect your fast-track income."),
    BoardSpace("Business", "FT_BUSINESS", "Buy a fast-track business opportunity."),
    BoardSpace("Dream", "DREAM", "Try to buy your chosen dream."),
    BoardSpace("Charity", "CHARITY", "Charity gives you an extra dice roll option."),
    BoardSpace("Tax Audit", "TAX_AUDIT", "A fast-track audit hits your cash."),
    BoardSpace("Lawsuit", "LAWSUIT", "Legal trouble drains your cash."),
    BoardSpace("Divorce", "DIVORCE", "A relationship breakdown costs everything."),
    BoardSpace("Cashflow Day", "CASHFLOW_DAY", "Collect your fast-track cashflow."),
]


def _small_deal_cards() -> List[DealCard]:
    return [
        DealCard(
            name="SIP in Nifty ETF",
            asset_type=AssetType.STOCK,
            cost=6000.0,
            down_payment=6000.0,
            monthly_cashflow=150.0,
            interest_rate=0.0,
            loan_months=0,
            description="Low-cost mutual fund SIP with steady dividend-like return.",
        ),
        DealCard(
            name="Chit Fund Scheme",
            asset_type=AssetType.CD,
            cost=5000.0,
            down_payment=5000.0,
            monthly_cashflow=120.0,
            interest_rate=0.0,
            loan_months=0,
            description="Short-term savings scheme with guaranteed payoff.",
        ),
        DealCard(
            name="Sarkari Scheme Investment",
            asset_type=AssetType.STOCK,
            cost=4500.0,
            down_payment=4500.0,
            monthly_cashflow=90.0,
            interest_rate=0.0,
            loan_months=0,
            description="Government-backed savings with stable returns.",
        ),
        DealCard(
            name="Franchise Corner Shop",
            asset_type=AssetType.BUSINESS,
            cost=8000.0,
            down_payment=2000.0,
            monthly_cashflow=250.0,
            interest_rate=0.10,
            loan_months=36,
            description="Small retail business with modest rental income.",
        ),
    ]


def _big_deal_cards() -> List[DealCard]:
    return [
        DealCard(
            name="Builder Floor Commercial Space",
            asset_type=AssetType.REAL_ESTATE,
            cost=120000.0,
            down_payment=30000.0,
            monthly_cashflow=4500.0,
            interest_rate=0.09,
            loan_months=180,
            description="High-value property offering strong rental cashflow.",
        ),
        DealCard(
            name="Organic Farm Business",
            asset_type=AssetType.AGRICULTURE if hasattr(AssetType, 'AGRICULTURE') else AssetType.OTHER,
            cost=90000.0,
            down_payment=25000.0,
            monthly_cashflow=3200.0,
            interest_rate=0.10,
            loan_months=120,
            description="Agriculture land with export-oriented income potential.",
        ),
        DealCard(
            name="Tech Startup Franchise",
            asset_type=AssetType.BUSINESS,
            cost=150000.0,
            down_payment=40000.0,
            monthly_cashflow=6200.0,
            interest_rate=0.11,
            loan_months=120,
            description="High-return franchise model in digital services.",
        ),
        DealCard(
            name="Luxury Apartment for Rent",
            asset_type=AssetType.REAL_ESTATE,
            cost=100000.0,
            down_payment=25000.0,
            monthly_cashflow=4700.0,
            interest_rate=0.08,
            loan_months=180,
            description="Premium real estate asset with strong rental demand.",
        ),
    ]


def _doodad_cards() -> List[DoodadCard]:
    return [
        DoodadCard(description="Festival shopping spree", cost=12000.0, payment_type="one_time"),
        DoodadCard(description="Medical emergency", cost=18000.0, payment_type="one_time"),
        DoodadCard(description="Wedding expense", cost=25000.0, payment_type="one_time"),
        DoodadCard(description="Monthly tuition increase", cost=1200.0, payment_type="monthly_increase", monthly_increase=1200.0),
        DoodadCard(description="Renovation bill", cost=8000.0, payment_type="one_time"),
    ]


def _market_cards() -> List[MarketCard]:
    return [
        MarketCard(description="Sensex surge lifts stock values", affects="stock", multiplier=1.20),
        MarketCard(description="Gold rally boosts gold returns", affects="gold", multiplier=1.25),
        MarketCard(description="FD maturity payout", affects="cd", multiplier=1.10),
        MarketCard(description="Real estate correction", affects="real_estate", multiplier=0.88),
        MarketCard(description="Selling opportunity for property cash", affects="real_estate", multiplier=1.15, sell_opportunity=True),
    ]


@dataclass
class TurnResult:
    rolled: int
    space: BoardSpace
    event: str
    card: Optional[object] = None
    entered_fast_track: bool = False
    win: bool = False
    bankrupt: bool = False


def _state_lists_to_tuples(value):
    if isinstance(value, (list, tuple)):
        return tuple(_state_lists_to_tuples(item) for item in value)
    return value


def _asset_from_snapshot(data: dict) -> Asset:
    return Asset(
        name=data["name"],
        asset_type=AssetType(data["asset_type"]),
        value=float(data["value"]),
        cashflow=float(data["cashflow"]),
        purchase_price=float(data["purchase_price"]),
        down_payment=float(data.get("down_payment", 0.0)),
        notes=data.get("notes", ""),
    )


def _liability_from_snapshot(data: dict) -> Liability:
    return Liability(
        name=data["name"],
        liability_type=LiabilityType(data["liability_type"]),
        principal=float(data["principal"]),
        monthly_payment=float(data["monthly_payment"]),
        interest_rate=float(data["interest_rate"]),
        remaining_months=int(data["remaining_months"]),
    )


def _player_from_snapshot(data: dict) -> Player:
    return Player(
        name=data["name"],
        profession=data["profession"],
        region=data["region"],
        salary=float(data["salary"]),
        taxes=float(data["taxes"]),
        other_expenses=float(data["other_expenses"]),
        children=int(data["children"]),
        child_cost_per_month=float(data["child_cost_per_month"]),
        cash=float(data["cash"]),
        position=int(data["position"]),
        ft_position=int(data["ft_position"]),
        on_fast_track=bool(data["on_fast_track"]),
        ft_monthly_income=float(data["ft_monthly_income"]),
        owns_dream=bool(data["owns_dream"]),
        dream_cost=float(data["dream_cost"]),
        bankrupt=bool(data["bankrupt"]),
        skip_turns=int(data["skip_turns"]),
        assets=[_asset_from_snapshot(asset) for asset in data["assets"]],
        liabilities=[_liability_from_snapshot(liability) for liability in data["liabilities"]],
    )


class CashflowGameEngine:
    def __init__(self, profession: str = "startup", region: str = "tier2", seed: int | None = None) -> None:
        self.seed = seed
        self._random = random.Random(seed)
        self.profession = profession
        self.region = region
        self.player = self._create_player(profession, region)
        self.board = RAT_RACE_BOARD
        self.fast_track_board = FAST_TRACK_BOARD
        self.small_deal_deck = _small_deal_cards()
        self.big_deal_deck = _big_deal_cards()
        self.doodad_deck = _doodad_cards()
        self.market_deck = _market_cards()
        self.last_event: str = "Game started."

    def _create_player(self, profession: str, region: str) -> Player:
        mapping = {
            "ias": {"salary": 90000.0, "other": 12000.0, "child_cost": 2500.0},
            "ca": {"salary": 70000.0, "other": 10000.0, "child_cost": 2200.0},
            "clerk": {"salary": 45000.0, "other": 9000.0, "child_cost": 1800.0},
            "startup": {"salary": 50000.0, "other": 14000.0, "child_cost": 2000.0},
            "kisan": {"salary": 30000.0, "other": 8000.0, "child_cost": 1600.0},
        }
        profile = mapping.get(profession.lower(), mapping["startup"])
        salary = profile["salary"] * (1.0 if region == "metro" else 0.9 if region == "tier2" else 0.75)
        cash = max(10000.0, salary * self._random.uniform(0.3, 0.6))
        player = Player(
            name=profession.capitalize(),
            profession=profession,
            region=region,
            salary=salary,
            taxes=0.0,
            other_expenses=profile["other"],
            children=0,
            child_cost_per_month=profile["child_cost"],
            cash=cash,
            dream_cost=250000.0,
        )
        player.recalculate()
        return player

    def roll_die(self, count: int = 1) -> int:
        return sum(self._random.randint(1, 6) for _ in range(count))

    def draw_card(self, deck_name: str):
        deck = {
            "SMALL_DEAL": self.small_deal_deck,
            "BIG_DEAL": self.big_deal_deck,
            "DOODAD": self.doodad_deck,
            "MARKET": self.market_deck,
        }[deck_name]
        if len(deck) == 0:
            return None
        return self._random.choice(deck)

    def take_turn(self) -> TurnResult:
        if self.player.bankrupt:
            return TurnResult(0, self.board[self.player.position], "Bankrupt—no more turns.", bankrupt=True)
        if self.player.skip_turns > 0:
            self.player.skip_turns -= 1
            return TurnResult(0, self.board[self.player.position], "You lose this turn due to downsizing.")

        roll = self.roll_die(1)
        self.player.position = (self.player.position + roll) % len(self.board)
        space = self.board[self.player.position]
        event = ""
        card = None

        if space.space_type == "PAYDAY":
            event = self.player.apply_payday()
        elif space.space_type in ("SMALL_DEAL", "BIG_DEAL"):
            card = self.draw_card(space.space_type)
            event = f"Landed on {space.name}. Opportunity card drawn: {card.description if card else 'none'}."
        elif space.space_type == "DOODAD":
            card = self.draw_card("DOODAD")
            event = self.apply_doodad_card(card)
        elif space.space_type == "MARKET":
            card = self.draw_card("MARKET")
            if card and card.sell_opportunity:
                event = f"Market card: {card.description} Choose whether to sell matching assets."
            else:
                event = self.apply_market_card(card)
        elif space.space_type == "BABY":
            event = self.add_child()
        elif space.space_type == "DOWNSIZED":
            event = self.downsized()
        elif space.space_type == "CHARITY":
            event = self.charity_offer()
        else:
            event = f"Landed on {space.name}."

        entered_fast = False
        if not self.player.on_fast_track and self.player.check_escape():
            self.player.on_fast_track = True
            self.player.ft_monthly_income = max(0.0, self.player.passive_income() * 100.0)
            entered_fast = True
            event += " Escape condition met! You can enter the Fast Track."

        self.last_event = event
        return TurnResult(roll, space, event, card, entered_fast, self.check_win(), self.player.bankrupt)

    def apply_deal_card(self, card: DealCard, accept: bool) -> str:
        if not accept or card is None:
            return "Deal ignored."
        if self.player.cash < card.down_payment:
            return "Not enough cash to pay the down payment."
        self.player.cash -= card.down_payment
        asset = Asset(
            name=card.name,
            asset_type=card.asset_type,
            value=card.cost,
            cashflow=card.monthly_cashflow,
            purchase_price=card.cost,
            down_payment=card.down_payment,
            notes=card.description,
        )
        self.player.add_asset(asset)
        if card.cost > card.down_payment and card.loan_months > 0:
            loan_principal = card.cost - card.down_payment
            monthly = loan_principal * 0.02
            liability = Liability(
                name=f"Loan for {card.name}",
                liability_type=LiabilityType.MORTGAGE if card.asset_type == AssetType.REAL_ESTATE else LiabilityType.BANK_LOAN,
                principal=loan_principal,
                monthly_payment=monthly,
                interest_rate=card.interest_rate,
                remaining_months=card.loan_months,
            )
            self.player.add_liability(liability)
        self.player.recalculate()
        return f"Purchased {card.name} with ₹{card.down_payment:,.0f} down payment."

    def apply_doodad_card(self, card: DoodadCard) -> str:
        if card is None:
            return "No doodad event."
        if card.payment_type == "one_time":
            self.player.cash -= card.cost
            if self.player.cash < 0 and not self.player.sell_assets_to_cover():
                self.player.bankrupt = True
                return f"Doodad: {card.description}. Could not pay {card.cost:,.0f}, bankrupt now."
            return f"Doodad: {card.description}. Paid ₹{card.cost:,.0f}."
        self.player.other_expenses += card.monthly_increase
        self.player.recalculate()
        return f"Doodad: {card.description}. Monthly expenses increased by ₹{card.monthly_increase:,.0f}."

    def apply_market_card(self, card: MarketCard) -> str:
        if card is None:
            return "No market event."
        affected = [a for a in self.player.assets if a.asset_type.value == card.affects or a.asset_type.value == card.affects.replace('_', ' ')]
        if not affected:
            return f"Market: {card.description}, but no matching assets were held."
        for asset in affected:
            asset.value *= card.multiplier
            asset.cashflow *= card.multiplier if asset.cashflow > 0 else 1.0
        self.player.recalculate()
        return f"Market: {card.description}. Updated {len(affected)} asset(s)."

    def add_child(self) -> str:
        self.player.children += 1
        self.player.recalculate()
        return f"Baby was born! Children count is now {self.player.children}. Monthly child expenses added."

    def downsized(self) -> str:
        self.player.skip_turns = 2
        reduction = self.player.salary * 0.25
        self.player.salary = max(0.0, self.player.salary - reduction)
        self.player.recalculate()
        return "Downsized: Salary reduced and two turns lost."

    def charity_offer(self) -> str:
        donation = min(self.player.cash * 0.05, 5000.0)
        self.player.cash -= donation
        if self.player.cash < 0:
            self.player.sell_assets_to_cover()
        return f"Charity: Donated ₹{donation:,.0f} and earned goodwill."

    def enter_fast_track(self) -> str:
        if not self.player.check_escape():
            return "Escape condition not met yet."
        self.player.on_fast_track = True
        self.player.ft_position = 0
        self.player.ft_monthly_income = max(0.0, self.player.passive_income() * 100.0)
        return "Entered Fast Track with a new fast-track income stream!"

    def fast_track_turn(self) -> TurnResult:
        if not self.player.on_fast_track:
            return TurnResult(0, self.board[self.player.position], "Not on Fast Track.")
        roll = self.roll_die(2)
        self.player.ft_position = (self.player.ft_position + roll) % len(self.fast_track_board)
        space = self.fast_track_board[self.player.ft_position]
        event = ""
        card = None

        if space.space_type == "CASHFLOW_DAY":
            amount = self.player.ft_monthly_income
            self.player.cash += amount
            event = f"Fast Track Cashflow Day: Received ₹{amount:,.0f}."
        elif space.space_type == "FT_BUSINESS":
            card = DealCard(
                name="Fast Track Solar Farm",
                asset_type=AssetType.BUSINESS,
                cost=120000.0,
                down_payment=30000.0,
                monthly_cashflow=8000.0,
                interest_rate=0.10,
                loan_months=120,
                description="High-yield clean energy business opportunity.",
            )
            event = "Fast Track Business space. You may choose to buy this opportunity."
        elif space.space_type == "DREAM":
            event = self.try_buy_dream()
        elif space.space_type == "CHARITY":
            self.player.cash -= min(self.player.cash * 0.05, 10000.0)
            event = "Fast Track Charity: Paid goodwill and earned a free extra roll next time."
        elif space.space_type == "TAX_AUDIT":
            loss = self.player.cash * 0.5
            self.player.cash -= loss
            event = f"Tax Audit: Paid ₹{loss:,.0f}."
        elif space.space_type == "LAWSUIT":
            loss = self.player.cash * 0.5
            self.player.cash -= loss
            event = f"Lawsuit: Paid ₹{loss:,.0f}."
        elif space.space_type == "DIVORCE":
            self.player.cash = 0.0
            event = "Divorce: Cash wiped out."
        else:
            event = f"Fast Track: {space.name}."

        self.player.recalculate()
        self.last_event = event
        return TurnResult(roll, space, event, card, False, self.check_win(), self.player.bankrupt)

    def try_buy_dream(self) -> str:
        if self.player.owns_dream:
            return "You already own your dream."
        if self.player.cash >= self.player.dream_cost:
            self.player.cash -= self.player.dream_cost
            self.player.owns_dream = True
            return f"Dream purchased for ₹{self.player.dream_cost:,.0f}!"
        return f"Fast Track Dream space: need ₹{self.player.dream_cost:,.0f}, you have ₹{self.player.cash:,.0f}."

    def purchase_fast_track_business(self, accept: bool) -> str:
        card = DealCard(
            name="Fast Track Solar Farm",
            asset_type=AssetType.BUSINESS,
            cost=120000.0,
            down_payment=30000.0,
            monthly_cashflow=8000.0,
            interest_rate=0.10,
            loan_months=120,
            description="High-yield clean energy business opportunity.",
        )
        return self.apply_deal_card(card, accept)

    def check_win(self) -> bool:
        return self.player.owns_dream or self.player.ft_monthly_income >= 50000.0

    def sell_asset(self, name: str) -> str:
        for asset in list(self.player.assets):
            if name.lower() in asset.name.lower():
                self.player.assets.remove(asset)
                self.player.cash += asset.value * 0.9
                self.player.recalculate()
                return f"Sold {asset.name} for ₹{asset.value * 0.9:,.0f}."
        return "Asset not found to sell."

    def state_snapshot(self) -> dict:
        return {
            "cash": self.player.cash,
            "salary": self.player.salary,
            "passive_income": self.player.passive_income(),
            "total_income": self.player.total_income(),
            "total_expenses": self.player.total_expenses(),
            "monthly_cashflow": self.player.monthly_cashflow(),
            "net_worth": self.player.net_worth(),
            "children": self.player.children,
            "assets": [a.to_dict() for a in self.player.assets],
            "liabilities": [l.to_dict() for l in self.player.liabilities],
            "position": self.player.position,
            "on_fast_track": self.player.on_fast_track,
            "ft_monthly_income": self.player.ft_monthly_income,
            "owns_dream": self.player.owns_dream,
            "bankrupt": self.player.bankrupt,
        }

    def persistence_snapshot(self) -> dict:
        player = self.player
        return {
            "version": 1,
            "profession": self.profession,
            "region": self.region,
            "player": {
                "name": player.name,
                "profession": player.profession,
                "region": player.region,
                "salary": player.salary,
                "taxes": player.taxes,
                "other_expenses": player.other_expenses,
                "children": player.children,
                "child_cost_per_month": player.child_cost_per_month,
                "cash": player.cash,
                "position": player.position,
                "ft_position": player.ft_position,
                "on_fast_track": player.on_fast_track,
                "ft_monthly_income": player.ft_monthly_income,
                "owns_dream": player.owns_dream,
                "dream_cost": player.dream_cost,
                "bankrupt": player.bankrupt,
                "skip_turns": player.skip_turns,
                "assets": [asset.to_dict() for asset in player.assets],
                "liabilities": [liability.to_dict() for liability in player.liabilities],
            },
            "random_state": self._random.getstate(),
            "last_event": self.last_event,
        }

    @classmethod
    def from_snapshot(cls, snapshot: dict) -> CashflowGameEngine:
        if not isinstance(snapshot, dict):
            raise ValueError("Cashflow save data must be an object.")

        version = snapshot.get("version")
        if version is None:
            engine = cls()
            player = engine.player
            player.cash = float(snapshot.get("cash", player.cash))
            player.salary = float(snapshot.get("salary", player.salary))
            player.children = int(snapshot.get("children", player.children))
            player.position = int(snapshot.get("position", player.position))
            player.on_fast_track = bool(snapshot.get("on_fast_track", player.on_fast_track))
            player.ft_position = int(snapshot.get("ft_position", player.ft_position))
            player.ft_monthly_income = float(snapshot.get("ft_monthly_income", player.ft_monthly_income))
            player.owns_dream = bool(snapshot.get("owns_dream", player.owns_dream))
            player.bankrupt = bool(snapshot.get("bankrupt", player.bankrupt))
            player.assets = [_asset_from_snapshot(asset) for asset in snapshot.get("assets", [])]
            player.liabilities = [
                _liability_from_snapshot(liability) for liability in snapshot.get("liabilities", [])
            ]
            return engine
        if type(version) is not int or version != 1:
            raise ValueError(f"Unsupported Cashflow save version: {version}.")

        engine = cls(
            profession=snapshot["profession"],
            region=snapshot["region"],
            seed=0,
        )
        engine.player = _player_from_snapshot(snapshot["player"])
        engine._random.setstate(_state_lists_to_tuples(snapshot["random_state"]))
        engine.last_event = snapshot["last_event"]
        return engine
