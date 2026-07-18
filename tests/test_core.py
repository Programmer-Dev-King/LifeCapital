import unittest
import os
import sys

# Ensure project root is on sys.path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from engine.india_data import income_tax_monthly, gst_effect_on_price, subsidy_for_sector
from engine.save_system import save_game, load_game
from engine.game_manager import GameManager


class TestIndiaData(unittest.TestCase):
    def test_tax_basic(self):
        # monthly income of 50k -> annual 600k -> tax should be >0
        tax = income_tax_monthly(50_000)
        self.assertGreater(tax, 0)

    def test_gst(self):
        price = gst_effect_on_price(0.18, 1000)
        self.assertAlmostEqual(price, 1180)

    def test_subsidy(self):
        val = subsidy_for_sector("agriculture")
        self.assertGreater(val, 0)


class TestSaveLoad(unittest.TestCase):
    def test_save_and_load(self):
        gm = GameManager()
        path = os.path.join(os.getcwd(), "testsave.json")
        save_game(path, gm.player, gm.economy.state)
        loaded = load_game(path)
        self.assertIsNotNone(loaded)
        player, econ = loaded
        self.assertEqual(player.name, gm.player.name)
        os.remove(path)


class TestSimulation(unittest.TestCase):
    def test_short_run(self):
        gm = GameManager()
        # run a short deterministic sim
        gm.economy = gm.economy.__class__(seed=123)
        gm.run_simulation(months=3)
        self.assertIsInstance(gm.player.cash, float)


if __name__ == "__main__":
    unittest.main()
