import unittest
import sqlite3
from backend import app as app_module


class ActionTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()

    def test_preview_and_sell(self):
        rv = self.client.post('/start', json={})
        self.assertEqual(rv.status_code, 200)
        d = rv.get_json()
        sid = d['session_id']
        token = d['token']

        # invest to create an asset
        rv2 = self.client.post('/action', json={"type": "invest_market", "symbol": "NIFTY_IND", "amount": 1000, "session_id": sid}, headers={"X-Session-Token": token})
        self.assertEqual(rv2.status_code, 200)
        d2 = rv2.get_json()
        asset = d2['asset']
        name = asset['name']

        # preview
        rv3 = self.client.post('/action/preview', json={"name": name, "session_id": sid}, headers={"X-Session-Token": token})
        self.assertEqual(rv3.status_code, 200)
        p = rv3.get_json()
        self.assertIn('proceeds', p)

        # sell
        rv4 = self.client.post('/action', json={"type": "sell_asset", "name": name, "session_id": sid}, headers={"X-Session-Token": token})
        self.assertEqual(rv4.status_code, 200)
        s4 = rv4.get_json()
        self.assertEqual(s4.get('status'), 'sold')


if __name__ == '__main__':
    unittest.main()
