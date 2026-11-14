import unittest
import hashlib
import json
import sqlite3
import uuid
from backend import app as app_module
from backend.admin import create_user, expire_all
from backend.security import hash_password
from engine.cashflow import Asset, AssetType, Liability, LiabilityType


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()
        self.username = f"auth-test-{uuid.uuid4().hex}"
        self.password = "correct horse battery"
        con = sqlite3.connect(app_module.DB_PATH)
        cur = con.cursor()
        cur.execute("DELETE FROM users WHERE username = 'admin'")
        cur.execute(
            "INSERT INTO users(username, pw_hash) VALUES (?, ?)",
            (self.username, hash_password(self.password)),
        )
        con.commit()
        con.close()

    def tearDown(self):
        con = sqlite3.connect(app_module.DB_PATH)
        con.execute("DELETE FROM users WHERE username = ?", (self.username,))
        con.commit()
        con.close()

    def test_login_requires_credentials_and_no_default_account(self):
        self.assertEqual(self.client.post('/auth/login', json={}).status_code, 400)
        legacy_admin_hash = hashlib.pbkdf2_hmac(
            "sha256", b"admin", b"static_salt_please_change", 100_000
        ).hex()
        con = sqlite3.connect(app_module.DB_PATH)
        con.execute(
            "INSERT OR REPLACE INTO users(username, pw_hash) VALUES ('admin', ?)",
            (legacy_admin_hash,),
        )
        con.commit()
        con.close()
        app_module._init_db()
        response = self.client.post('/auth/login', json={"username": "admin", "password": "admin"})
        self.assertEqual(response.status_code, 401)

    def test_admin_created_user_can_log_in(self):
        create_user(self.username, self.password)
        response = self.client.post(
            '/auth/login',
            json={"username": self.username, "password": self.password},
        )
        self.assertEqual(response.status_code, 200)

    def test_login_and_refresh_and_expiry(self):
        rv = self.client.post('/auth/login', json={"username": self.username, "password": self.password})
        self.assertEqual(rv.status_code, 200)
        data = rv.get_json()
        self.assertIn('session_id', data)
        self.assertIn('token', data)
        sid = data['session_id']
        token = data['token']

        con = sqlite3.connect(app_module.DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT token FROM sessions WHERE session_id = ?", (sid,))
        stored_token = cur.fetchone()[0]
        con.close()
        self.assertNotEqual(stored_token, token)

        # refresh should extend expiry
        rv2 = self.client.post('/auth/refresh', json={"session_id": sid}, headers={"X-Session-Token": token})
        self.assertEqual(rv2.status_code, 200)
        d2 = rv2.get_json()
        self.assertEqual(d2.get('status'), 'refreshed')

        con = sqlite3.connect(app_module.DB_PATH)
        cur = con.cursor()
        cur.execute("UPDATE sessions SET token_expires = datetime('now', '-1 day') WHERE session_id = ?", (sid,))
        con.commit()
        con.close()

        rv3 = self.client.get('/state', query_string={"session_id": sid}, headers={"X-Session-Token": token})
        self.assertEqual(rv3.status_code, 401)

    def test_simulator_requires_matching_session_token(self):
        started = self.client.post('/session', json={}).get_json()
        sid = started["session_id"]
        token = started["token"]

        self.assertEqual(self.client.get('/state', query_string={"session_id": sid}).status_code, 401)
        self.assertEqual(
            self.client.get('/state', query_string={"session_id": sid}, headers={"X-Session-Token": "wrong"}).status_code,
            401,
        )
        self.assertEqual(
            self.client.get('/state', query_string={"session_id": sid}, headers={"X-Session-Token": token}).status_code,
            200,
        )

    def test_cashflow_requires_matching_session_token(self):
        started = self.client.post('/cashflow/start', json={"seed": 1}).get_json()
        sid = started["session_id"]
        token = started["token"]
        path = '/cashflow/turn'

        con = sqlite3.connect(app_module.DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT token FROM cashflow_sessions WHERE session_id = ?", (sid,))
        self.assertNotEqual(cur.fetchone()[0], token)
        con.close()

        self.assertEqual(self.client.post(path, json={"session_id": sid}).status_code, 401)
        self.assertEqual(
            self.client.post(path, json={"session_id": sid}, headers={"X-Session-Token": "wrong"}).status_code,
            401,
        )
        self.assertEqual(
            self.client.post(path, json={"session_id": sid}, headers={"X-Session-Token": token}).status_code,
            200,
        )

    def test_cashflow_session_restores_full_state_after_restart(self):
        started = self.client.post(
            '/cashflow/start',
            json={"profession": "ca", "region": "metro", "seed": 42},
        ).get_json()
        sid = started["session_id"]
        token = started["token"]
        engine = app_module._cashflow_sessions[sid]["engine"]
        player = engine.player
        player.cash = 123456.0
        player.salary = 76543.0
        player.taxes = 4321.0
        player.other_expenses = 8765.0
        player.children = 2
        player.child_cost_per_month = 2345.0
        player.position = 9
        player.ft_position = 3
        player.on_fast_track = True
        player.ft_monthly_income = 90000.0
        player.owns_dream = True
        player.dream_cost = 125000.0
        player.skip_turns = 1
        player.assets = [
            Asset(
                name="Snapshot rental",
                asset_type=AssetType.REAL_ESTATE,
                value=200000.0,
                cashflow=5000.0,
                purchase_price=180000.0,
                down_payment=50000.0,
                notes="Persistence regression test",
            )
        ]
        player.liabilities = [
            Liability(
                name="Snapshot mortgage",
                liability_type=LiabilityType.MORTGAGE,
                principal=100000.0,
                monthly_payment=1200.0,
                interest_rate=0.08,
                remaining_months=120,
            )
        ]
        engine.last_event = "Persisted test event."
        expected = engine.persistence_snapshot()

        with sqlite3.connect(app_module.DB_PATH) as con:
            con.execute(
                "UPDATE cashflow_sessions SET game_state = ? WHERE session_id = ?",
                (json.dumps(expected), sid),
            )
        app_module._cashflow_sessions.pop(sid, None)

        restored, _ = app_module._get_cashflow_session(sid, token)
        restored_engine = restored["engine"]
        self.assertEqual(expected, restored_engine.persistence_snapshot())
        self.assertEqual(engine.roll_die(), restored_engine.roll_die())

    def test_load_requires_an_authenticated_session(self):
        response = self.client.post('/load', json={"session_id": "untrusted"})
        self.assertEqual(response.status_code, 401)

    def test_expire_all_revokes_active_sessions(self):
        simulator = self.client.post('/session', json={}).get_json()
        cashflow = self.client.post('/cashflow/start', json={"seed": 2}).get_json()
        expire_all()

        self.assertEqual(
            self.client.get(
                '/state',
                query_string={"session_id": simulator["session_id"]},
                headers={"X-Session-Token": simulator["token"]},
            ).status_code,
            401,
        )
        self.assertEqual(
            self.client.post(
                '/cashflow/turn',
                json={"session_id": cashflow["session_id"]},
                headers={"X-Session-Token": cashflow["token"]},
            ).status_code,
            401,
        )


if __name__ == '__main__':
    unittest.main()
