import unittest
import time
import sqlite3
from backend import app as app_module


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()

    def test_login_and_refresh_and_expiry(self):
        # login with default admin
        rv = self.client.post('/auth/login', json={"username": "admin", "password": "admin"})
        self.assertEqual(rv.status_code, 200)
        data = rv.get_json()
        self.assertIn('session_id', data)
        self.assertIn('token', data)
        sid = data['session_id']
        token = data['token']

        # refresh should extend expiry
        rv2 = self.client.post('/auth/refresh', json={"session_id": sid}, headers={"X-Session-Token": token})
        self.assertEqual(rv2.status_code, 200)
        d2 = rv2.get_json()
        self.assertEqual(d2.get('status'), 'refreshed')

        # force expiry by updating DB
        con = sqlite3.connect(app_module.DB_PATH)
        cur = con.cursor()
        cur.execute("UPDATE sessions SET token_expires = datetime('now', '-1 day') WHERE session_id = ?", (sid,))
        con.commit()
        con.close()

        # now state should fail due to expired token
        rv3 = self.client.get('/state', query_string={"session_id": sid}, headers={"X-Session-Token": token})
        self.assertNotEqual(rv3.status_code, 200)


if __name__ == '__main__':
    unittest.main()
