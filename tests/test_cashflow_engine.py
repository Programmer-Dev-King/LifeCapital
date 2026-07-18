import unittest

from engine.cashflow import CashflowGameEngine, AssetType, Asset, Liability


class CashflowEngineTests(unittest.TestCase):
    def test_escape_condition_and_fast_track_entry(self):
        engine = CashflowGameEngine(profession="kisan", region="tier2", seed=123)
        engine.player.cash += 50000.0
        # add passive assets to exceed expenses
        asset = Asset(
            name="Test Rental",
            asset_type=AssetType.REAL_ESTATE,
            value=20000.0,
            cashflow=10000.0,
            purchase_price=20000.0,
            down_payment=20000.0,
            notes="Test asset.",
        )
        engine.player.add_asset(asset)
        self.assertTrue(engine.player.check_escape())
        result = engine.take_turn()
        self.assertTrue(result.entered_fast_track)
        self.assertTrue(engine.player.on_fast_track)

    def test_doodad_and_bankruptcy(self):
        engine = CashflowGameEngine(profession="clerk", region="rural", seed=1)
        engine.player.cash = 1000.0
        card = engine.player.recalculate()
        self.assertIsNone(card)
        # force a doodad event with high cost
        from engine.cashflow import DoodadCard

        doodad = DoodadCard(description="Emergency bill", cost=20000.0, payment_type="one_time")
        event = engine.apply_doodad_card(doodad)
        self.assertTrue("bankrupt" in event.lower() or engine.player.bankrupt)

    def test_sell_asset(self):
        engine = CashflowGameEngine(profession="startup", region="metro", seed=42)
        asset = Asset(
            name="Sell Test Business",
            asset_type=AssetType.BUSINESS,
            value=20000.0,
            cashflow=500.0,
            purchase_price=20000.0,
            down_payment=20000.0,
            notes="Test asset for selling.",
        )
        engine.player.add_asset(asset)
        asset_name = engine.player.assets[0].name
        result = engine.sell_asset(asset_name)
        self.assertIn("Sold", result)


if __name__ == "__main__":
    unittest.main()
