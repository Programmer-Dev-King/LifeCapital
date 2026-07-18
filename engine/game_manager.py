from __future__ import annotations

from .player import Player
from .economy import EconomyManager
from .events import EventManager
from .assets import Asset, AssetType, Liability, LiabilityType
from .market import MarketManager
from .ai_manager import AIManager


class GameManager:
    def __init__(self) -> None:
        self.economy = EconomyManager()
        self.events = EventManager()
        self.market = MarketManager()
        self.ai = AIManager()
        self.player = Player(
            name="Player1",
            cash=50_000.0,
            monthly_income=30_000.0,
            passive_income=0.0,
            expenses=18_000.0,
            credit_score=650,
            risk_appetite=0.4,
            reputation=0.5,
        )
        ef = Asset(name="Emergency Fund", asset_type=AssetType.ETF, value=30_000.0, monthly_cashflow=0.0, risk=0.05, growth_bias=0.01)
        self.player.add_asset(ef)

    def start(self, months: int = 36, interactive: bool = False) -> None:
        mode = "Interactive" if interactive else "Auto"
        print(f"Starting LifeCapital demo run ({months} months) - Mode: {mode}...")
        self.run_simulation(months=months, interactive=interactive)

    def execute_action(self, action: dict) -> dict:
        result = {"type": action.get("type"), "success": False}
        if action.get("type") == "invest_market":
            amount = float(action.get("amount", 0.0))
            if amount > 0 and self.player.cash >= amount:
                symbol = action.get("symbol", "NIFTY_IND")
                asset = self.market.create_asset_from_symbol(symbol, amount)
                self.player.cash -= amount
                self.player.add_asset(asset)
                result.update({"success": True, "asset": asset})
        elif action.get("type") == "buy_rental":
            amount = float(action.get("amount", 0.0))
            if amount > 0 and self.player.cash >= amount:
                rental = Asset(
                    name=f"Rental Prop {len(self.player.assets) + 1}",
                    asset_type=AssetType.RENTAL,
                    value=amount,
                    monthly_cashflow=amount * 0.004,
                    risk=0.15,
                    growth_bias=0.02,
                )
                self.player.cash -= amount
                self.player.add_asset(rental)
                result.update({"success": True, "asset": rental})
        elif action.get("type") == "take_loan":
            amount = float(action.get("amount", 0.0))
            if amount > 0:
                monthly = amount / 120.0
                li = Liability(
                    name="Personal Loan",
                    liability_type=LiabilityType.BUSINESS_LOAN,
                    principal=amount,
                    monthly_payment=monthly,
                    interest_rate=self.economy.state.interest_rate,
                    remaining_months=120,
                )
                self.player.cash += amount
                self.player.add_liability(li)
                result.update({"success": True, "liability": li})
        else:
            result["success"] = True
        return result

    def step_month(self, action: dict | None = None) -> dict:
        self.economy.step()
        event_text, event_data = self.events.generate_event(self.economy, self.player)
        result = {"action_applied": None}
        if action:
            result["action_applied"] = self.execute_action(action)

        for a in self.player.assets:
            mult = self.economy.asset_multiplier(a.asset_type.value, a.risk)
            a.update_value(mult)
            if a.asset_type == AssetType.RENTAL and a.monthly_cashflow == 0:
                a.monthly_cashflow = max(0.0, a.value * 0.004)

        self.player.apply_month()
        return {
            "event_text": event_text,
            "event_data": event_data,
            "player": self.player.to_dict(),
            "economy": self.economy.state.__dict__,
            **result,
        }

    def run_simulation(self, months: int = 36, interactive: bool = False) -> None:
        for m in range(1, months + 1):
            action = {"type": "pass"}
            if interactive:
                print("Choose action: 1) Pass  2) Invest Index  3) Buy Rental  4) Take Loan")
                ch = input("Enter 1-4: ")
                if ch == "2":
                    amt = min(self.player.cash * 0.5, self.player.cash)
                    action = {"type": "invest_market", "symbol": "NIFTY_IND", "amount": amt}
                elif ch == "3":
                    amt = min(self.player.cash, 100_000.0)
                    action = {"type": "buy_rental", "amount": amt}
                elif ch == "4":
                    amt = 100_000.0
                    action = {"type": "take_loan", "amount": amt}
            else:
                action = self.ai.decide(self.player, self.economy.state)

            month_data = self.step_month(action)
            s = self.economy.state
            print(f"Month {m:02d}: {month_data['event_text']}")
            print(f" Economy: Inflation {s.inflation:.2%}, Interest {s.interest_rate:.2%}, StockIdx {s.stock_index:,.0f}, REIdx {s.real_estate_index:,.0f}")
            print(f" {self.player}")
            print(f" Assets: {len(self.player.assets)}, Liabilities: {len(self.player.liabilities)}\n")

        print("--- Simulation Complete ---")
        print(f"Final player state: {self.player}")
        print("Top assets:")
        for a in sorted(self.player.assets, key=lambda x: x.value, reverse=True)[:5]:
            print(f" - {a}")
