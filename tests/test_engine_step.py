import unittest
from engine.game_manager import GameManager


class TestGameManagerStep(unittest.TestCase):
    def test_step_month_returns_structure(self):
        gm = GameManager()
        # ensure deterministic-ish by setting small seed
        gm.economy = gm.economy.__class__(seed=42)
        result = gm.step_month()
        self.assertIsInstance(result, dict)
        self.assertIn("event_text", result)
        self.assertIn("event_data", result)
        self.assertIn("player", result)
        self.assertIn("economy", result)


if __name__ == "__main__":
    unittest.main()
