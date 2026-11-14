from flask import Flask, request, jsonify
from engine.game_manager import GameManager
from engine.india_data import sample_starting_profile
from engine.market import MarketManager
from engine.save_system import save_game, load_game
from engine.cashflow import CashflowGameEngine
from engine.cashflow_indian_decks import get_indian_small_deals, get_indian_big_deals, get_indian_doodads, get_indian_markets
import threading
import os
import uuid
import sqlite3
import secrets
import json
import hashlib
from contextlib import closing
from pathlib import Path
from typing import Optional
from backend.security import hash_password, hash_session_token, password_needs_rehash, session_token_matches, verify_password

app = Flask(__name__)

_sessions: dict[str, dict] = {}
_cashflow_sessions: dict[str, dict] = {}


# Simple SQLite-based session store for persistence
DB_PATH = os.environ.get(
    "LIFECAP_DB_PATH",
    str(Path(__file__).resolve().parent.parent / "lifecycle_sessions.db"),
)

def _init_db() -> None:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            token TEXT,
            player_json TEXT,
            economy_json TEXT,
            created_at TEXT,
            last_active TEXT,
            token_expires TEXT
        )
        """
    )
    # users table for simple credential demo
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            pw_hash TEXT
        )
        """
    )
    legacy_salts = {
        "static_salt_please_change",
        os.environ.get("LIFECAP_SALT", ""),
        os.environ.get("LIFECAP_LEGACY_SALT", ""),
    }
    for legacy_salt in legacy_salts - {""}:
        default_admin_hash = hashlib.pbkdf2_hmac(
            "sha256", b"admin", legacy_salt.encode("utf-8"), 100_000
        ).hex()
        cur.execute("DELETE FROM users WHERE username = 'admin' AND pw_hash = ?", (default_admin_hash,))
    # cashflow game sessions
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS cashflow_sessions (
            session_id TEXT PRIMARY KEY,
            token TEXT,
            game_state TEXT,
            created_at TEXT,
            last_active TEXT,
            token_expires TEXT
        )
        """
    )
    con.commit()
    con.close()


def _save_session_db(session_id: str, token_hash: str, player_json: str, economy_json: str, created_at: str | None = None, last_active: str | None = None, token_expires: str | None = None) -> None:
    import datetime

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    # preserve created_at and token_expires if they exist
    cur.execute("SELECT created_at, token_expires FROM sessions WHERE session_id = ?", (session_id,))
    row = cur.fetchone()
    if row and not created_at:
        created = row[0]
    else:
        created = created_at or now
    la = last_active or now
    if token_expires is None:
        if row and row[1]:
            token_expires = row[1]
        else:
            token_expires = (datetime.datetime.fromisoformat(la) + datetime.timedelta(hours=24)).isoformat()
    cur.execute(
        "REPLACE INTO sessions(session_id, token, player_json, economy_json, created_at, last_active, token_expires) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (session_id, token_hash, player_json, economy_json, created, la, token_expires),
    )
    con.commit()
    con.close()


def _load_session_db(session_id: str) -> Optional[dict]:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT session_id, token, player_json, economy_json, created_at, last_active, token_expires FROM sessions WHERE session_id = ?", (session_id,))
    row = cur.fetchone()
    con.close()
    if not row:
        return None
    return {
        "session_id": row[0],
        "token_hash": row[1],
        "player_json": row[2],
        "economy_json": row[3],
        "created_at": row[4],
        "last_active": row[5],
        "token_expires": row[6],
    }


# initialize DB on import
_init_db()


def get_session(session_id: str | None):
    if not session_id:
        return None
    return _sessions.get(session_id)


def current_session():
    data = request.get_json(silent=True) or {}
    session_id = request.args.get("session_id") or data.get("session_id")
    token = request.headers.get("X-Session-Token") or data.get("token")
    if not session_id or not token:
        return None, session_id

    sess = get_session(session_id)
    if not sess and session_id:
        row = _load_session_db(session_id)
        if not row or not session_token_matches(token, row.get("token_hash")):
            return None, session_id
        import datetime
        from engine.player import Player

        try:
            exp = datetime.datetime.fromisoformat(row["token_expires"])
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=datetime.timezone.utc)
            if datetime.datetime.now(datetime.timezone.utc) > exp:
                return None, session_id
            gm = GameManager()
            gm.player = Player.from_dict(json.loads(row["player_json"]))
            gm.economy.state = type(gm.economy.state)(**json.loads(row["economy_json"]))
        except (KeyError, TypeError, ValueError):
            return None, session_id
        _sessions[session_id] = {
            "game": gm,
            "lock": threading.Lock(),
            "token_hash": row["token_hash"],
            "token_expires": row["token_expires"],
        }
        sess = _sessions[session_id]

    if not sess or not session_token_matches(token, sess.get("token_hash")):
        return None, session_id

    if sess:
        import datetime

        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT token, token_expires FROM sessions WHERE session_id = ?", (session_id,))
        row = cur.fetchone()
        con.close()
        if not row or row[0] != sess["token_hash"]:
            _sessions.pop(session_id, None)
            return None, session_id
        try:
            exp = datetime.datetime.fromisoformat(row[1])
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=datetime.timezone.utc)
        except (TypeError, ValueError):
            _sessions.pop(session_id, None)
            return None, session_id
        if datetime.datetime.now(datetime.timezone.utc) > exp:
            _sessions.pop(session_id, None)
            return None, session_id
        sess["token_expires"] = row[1]
        _save_session_db(
            session_id,
            sess["token_hash"],
            json.dumps(sess["game"].player.to_dict()),
            json.dumps(sess["game"].economy.state.__dict__),
        )
    return sess, session_id



@app.route("/action/preview", methods=["POST"])
def action_preview():
    data = request.get_json(silent=True) or {}
    session, session_id = current_session()
    if not session:
        return jsonify({"error": "invalid or expired session"}), 401
    gm = session["game"]
    act = data.get("type") or data.get("action") or "preview_sell"
    if act in ("preview_sell", "sell_preview") or data.get("name"):
        name = data.get("name", "")
        found = None
        for a in gm.player.assets:
            if name and name in a.name:
                found = a
                break
        if not found:
            return jsonify({"error": "asset not found"}), 404
        proceeds = max(0.0, found.value * 0.99)
        return jsonify({"status": "preview", "asset": found.to_dict(), "proceeds": proceeds, "session_id": session_id})
    return jsonify({"error": "unknown preview"}), 400


def serialize_player(player):
    return {
        "name": player.name,
        "cash": player.cash,
        "monthly_income": player.monthly_income,
        "passive_income": player.passive_income,
        "expenses": player.expenses,
        "credit_score": player.credit_score,
        "risk_appetite": player.risk_appetite,
        "reputation": player.reputation,
        "region": getattr(player, "region", "tier2"),
        "education": getattr(player, "education", "graduate"),
        "age": getattr(player, "age", 25),
        "dependents": getattr(player, "dependents", 0),
        "net_worth": player.net_worth(),
        "assets": [a.to_dict() for a in player.assets],
        "liabilities": [l.to_dict() for l in player.liabilities],
    }


def serialize_economy(state):
    return {
        "month": state.month,
        "inflation": state.inflation,
        "interest_rate": state.interest_rate,
        "unemployment_rate": state.unemployment_rate,
        "real_estate_index": state.real_estate_index,
        "stock_index": state.stock_index,
        "gdp_growth": state.gdp_growth,
        "market_sentiment": state.market_sentiment,
    }


@app.route("/session", methods=["POST"])
def create_session():
    data = request.get_json(silent=True) or {}
    profile = data.get("profile", {})
    starting_profile = sample_starting_profile(
        region=profile.get("region", "tier2"),
        education=profile.get("education", "graduate"),
    )

    gm = GameManager()
    gm.player.cash = starting_profile["cash"]
    gm.player.monthly_income = starting_profile["monthly_income"]
    gm.player.expenses = starting_profile["expenses"]
    gm.player.region = starting_profile["region"]
    gm.player.education = starting_profile["education"]
    gm.player.age = starting_profile["age"]
    gm.player.dependents = starting_profile["dependents"]
    if profile.get("name"):
        gm.player.name = profile["name"]

    session_id = str(uuid.uuid4())
    token = secrets.token_hex(16)
    token_hash = hash_session_token(token)
    _sessions[session_id] = {"game": gm, "lock": threading.Lock(), "token_hash": token_hash}
    # persist minimal snapshot
    import json, datetime

    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat()
    _save_session_db(session_id, token_hash, json.dumps(gm.player.to_dict()), json.dumps(gm.economy.state.__dict__), now, now)
    return jsonify({
        "status": "started",
        "session_id": session_id,
        "token": token,
        "player": serialize_player(gm.player),
        "economy": serialize_economy(gm.economy.state),
    })


@app.route("/auth/login", methods=["POST"])
def auth_login():
    """Authenticate an existing user and create a game session."""
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    if not isinstance(username, str) or not username or not isinstance(password, str) or not password:
        return jsonify({"error": "username and password are required"}), 400
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT pw_hash FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    if not row or not verify_password(password, row[0], os.environ.get("LIFECAP_LEGACY_SALT")):
        con.close()
        return jsonify({"error": "invalid credentials"}), 401
    if password_needs_rehash(row[0]):
        if len(password) < 12:
            con.close()
            return jsonify({"error": "password reset required"}), 403
        cur.execute("UPDATE users SET pw_hash = ? WHERE username = ?", (hash_password(password), username))
        con.commit()
    con.close()
    return create_session()


@app.route("/auth/refresh", methods=["POST"])
def auth_refresh():
    data = request.get_json(silent=True) or {}
    session_id = request.args.get("session_id") or data.get("session_id")
    token = request.headers.get("X-Session-Token") or data.get("token")
    row = _load_session_db(session_id)
    if not row or not session_token_matches(token, row.get("token_hash")):
        return jsonify({"error": "invalid session"}), 401
    import datetime
    try:
        expires_at = datetime.datetime.fromisoformat(row["token_expires"])
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "invalid session"}), 401
    if datetime.datetime.now(datetime.timezone.utc) > expires_at:
        return jsonify({"error": "invalid session"}), 401

    new_expires = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)).isoformat()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("UPDATE sessions SET token_expires = ? WHERE session_id = ?", (new_expires, session_id))
    con.commit()
    con.close()
    return jsonify({"status": "refreshed", "token_expires": new_expires})


@app.route("/auth/logout", methods=["POST"])
def auth_logout():
    data = request.get_json(silent=True) or {}
    session_id = request.args.get("session_id") or data.get("session_id")
    token = request.headers.get("X-Session-Token") or data.get("token")
    sess = get_session(session_id)
    # If not in memory, try load
    if not sess:
        row = _load_session_db(session_id)
        if row and session_token_matches(token, row.get("token_hash")):
            # delete DB row
            con = sqlite3.connect(DB_PATH)
            cur = con.cursor()
            cur.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            con.commit()
            con.close()
            return jsonify({"status": "logged_out", "session_id": session_id})
    else:
        if session_token_matches(token, sess.get("token_hash")):
            # remove in-memory and DB
            _sessions.pop(session_id, None)
            con = sqlite3.connect(DB_PATH)
            cur = con.cursor()
            cur.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            con.commit()
            con.close()
            return jsonify({"status": "logged_out", "session_id": session_id})
    return jsonify({"error": "invalid session or token"}), 401


def _expire_old_sessions(ttl_seconds: int) -> int:
    """Expire sessions with last_active older than TTL (seconds). Returns count expired."""
    import datetime

    cutoff = (
        datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        - datetime.timedelta(seconds=ttl_seconds)
    ).isoformat()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT session_id FROM sessions WHERE last_active < ? OR token_expires < ?", (cutoff, cutoff))
    rows = cur.fetchall()
    ids = [r[0] for r in rows]
    for sid in ids:
        _sessions.pop(sid, None)
    cur.execute("DELETE FROM sessions WHERE last_active < ?", (cutoff,))
    cur.execute("DELETE FROM sessions WHERE token_expires < ?", (cutoff,))
    con.commit()
    con.close()
    return len(ids)


def _start_cleanup_thread(interval_seconds: int = 300, ttl_seconds: int = 3600 * 24):
    import threading, time

    def _worker():
        while True:
            try:
                _expire_old_sessions(ttl_seconds)
            except Exception:
                pass
            time.sleep(interval_seconds)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


# kick off background cleanup
_start_cleanup_thread()


@app.route("/start", methods=["POST"])
def start():
    return create_session()


@app.route("/state", methods=["GET"])
def state():
    session, session_id = current_session()
    if not session:
        return jsonify({"error": "invalid or expired session"}), 401
    gm = session["game"]
    return jsonify({
        "session_id": session_id,
        "player": serialize_player(gm.player),
        "economy": serialize_economy(gm.economy.state),
    })


@app.route("/market", methods=["GET"])
def market():
    session, session_id = current_session()
    if session:
        market_inst = session["game"].market.list_marketable()
    else:
        market_inst = MarketManager().list_marketable()
    return jsonify({"session_id": session_id, "instruments": market_inst})


@app.route("/action", methods=["POST"])
def action():
    data = request.get_json(silent=True) or {}
    session, session_id = current_session()
    if not session:
        return jsonify({"error": "invalid or expired session"}), 401
    gm = session["game"]
    lock = session["lock"]

    with lock:
        act_type = data.get("type")
        # support selling assets (simple prototype): compute server-side proceeds and remove asset
        if act_type == "sell_asset":
            name = data.get("name", "")
            # find by name substring
            removed = None
            for a in list(gm.player.assets):
                if name and name in a.name:
                    removed = a
                    break
            if not removed:
                return jsonify({"error": "asset not found", "session_id": session_id}), 400
            try:
                # pricing: current value minus 1% fee
                proceeds = max(0.0, removed.value * 0.99)
                gm.player.assets.remove(removed)
                gm.player.cash += proceeds
                # persist
                import json

                _save_session_db(session_id, session["token_hash"], json.dumps(gm.player.to_dict()), json.dumps(gm.economy.state.__dict__))
            except Exception:
                pass
            return jsonify({"status": "sold", "proceeds": proceeds, "asset": removed.to_dict(), "player": serialize_player(gm.player), "session_id": session_id})
        if act_type == "invest_market":
            symbol = data.get("symbol", "NIFTY_IND")
            amount = float(data.get("amount", 0.0))
            if amount <= 0 or amount > gm.player.cash:
                return jsonify({"error": "invalid amount", "session_id": session_id}), 400
            asset = gm.market.create_asset_from_symbol(symbol, amount)
            gm.player.cash -= amount
            gm.player.add_asset(asset)
            # persist snapshot
            try:
                import json

                _save_session_db(session_id, session["token_hash"], json.dumps(gm.player.to_dict()), json.dumps(gm.economy.state.__dict__))
            except Exception:
                pass
            return jsonify({
                "status": "invested",
                "asset": asset.to_dict(),
                "player": serialize_player(gm.player),
                "economy": serialize_economy(gm.economy.state),
                "session_id": session_id,
            })

        if act_type == "buy_rental":
            amount = float(data.get("amount", 0.0))
            if amount <= 0 or amount > gm.player.cash:
                return jsonify({"error": "invalid amount", "session_id": session_id}), 400
            from engine.assets import Asset, AssetType
            rental = Asset(
                name=f"Rental Prop {len(gm.player.assets) + 1}",
                asset_type=AssetType.RENTAL,
                value=amount,
                monthly_cashflow=amount * 0.004,
                risk=0.15,
                growth_bias=0.02,
            )
            gm.player.cash -= amount
            gm.player.add_asset(rental)
            try:
                import json

                _save_session_db(session_id, session["token_hash"], json.dumps(gm.player.to_dict()), json.dumps(gm.economy.state.__dict__))
            except Exception:
                pass
            return jsonify({
                "status": "bought_rental",
                "asset": rental.to_dict(),
                "player": serialize_player(gm.player),
                "economy": serialize_economy(gm.economy.state),
                "session_id": session_id,
            })

        if act_type == "take_loan":
            amount = float(data.get("amount", 0.0))
            if amount <= 0:
                return jsonify({"error": "invalid amount", "session_id": session_id}), 400
            from engine.assets import Liability, LiabilityType
            monthly = amount / 120.0
            li = Liability(
                name="Personal Loan",
                liability_type=LiabilityType.BUSINESS_LOAN,
                principal=amount,
                monthly_payment=monthly,
                interest_rate=gm.economy.state.interest_rate,
                remaining_months=120,
            )
            gm.player.cash += amount
            gm.player.add_liability(li)
            try:
                import json

                _save_session_db(session_id, session["token_hash"], json.dumps(gm.player.to_dict()), json.dumps(gm.economy.state.__dict__))
            except Exception:
                pass
            return jsonify({
                "status": "loan_taken",
                "liability": li.to_dict(),
                "player": serialize_player(gm.player),
                "economy": serialize_economy(gm.economy.state),
                "session_id": session_id,
            })

        return jsonify({"error": "unknown action", "session_id": session_id}), 400


@app.route("/step", methods=["POST"])
def step():
    data = request.get_json(silent=True) or {}
    session, session_id = current_session()
    if not session:
        return jsonify({"error": "invalid or expired session"}), 401
    gm = session["game"]
    months = int(data.get("months", 1))
    events = []
    for _ in range(months):
        events.append(gm.step_month())
        # persist after each month
        try:
            import json

            _save_session_db(session_id, session["token_hash"], json.dumps(gm.player.to_dict()), json.dumps(gm.economy.state.__dict__))
        except Exception:
            pass
    return jsonify({
        "status": "stepped",
        "events": events,
        "player": serialize_player(gm.player),
        "economy": serialize_economy(gm.economy.state),
        "session_id": session_id,
    })


@app.route("/save", methods=["POST"])
def save():
    session, session_id = current_session()
    if not session:
        return jsonify({"error": "invalid or expired session"}), 401
    gm = session["game"]
    save_path = os.path.join(os.getcwd(), f"savegame_{session_id}.json")
    save_game(save_path, gm.player, gm.economy.state)
    return jsonify({"status": "saved", "path": save_path, "session_id": session_id})


@app.route("/load", methods=["POST"])
def load():
    session, session_id = current_session()
    if not session:
        return jsonify({"error": "invalid or expired session"}), 401
    save_path = os.path.join(os.getcwd(), f"savegame_{session_id}.json")
    loaded = load_game(save_path)
    if not loaded:
        return jsonify({"error": "no save", "session_id": session_id}), 404
    player, econ = loaded
    with session["lock"]:
        session["game"].player = player
        session["game"].economy.state = econ
    return jsonify({
        "status": "loaded",
        "session_id": session_id,
        "player": serialize_player(session["game"].player),
        "economy": serialize_economy(session["game"].economy.state),
    })


# ============ Cashflow Game Routes ============


def _persist_cashflow_state(session_id: str, engine: CashflowGameEngine) -> None:
    with closing(sqlite3.connect(DB_PATH)) as con:
        with con:
            cur = con.execute(
                "UPDATE cashflow_sessions SET game_state = ? WHERE session_id = ?",
                (json.dumps(engine.persistence_snapshot()), session_id),
            )
            if cur.rowcount != 1:
                raise RuntimeError("The Cashflow session no longer exists in the database.")


@app.route("/cashflow/start", methods=["POST"])
def cashflow_start():
    """Start a new Cashflow game session."""
    data = request.get_json(silent=True) or {}
    profession = data.get("profession", "startup")
    region = data.get("region", "tier2")
    seed = data.get("seed")
    
    engine = CashflowGameEngine(profession=profession, region=region, seed=seed)
    session_id = str(uuid.uuid4())
    token = secrets.token_hex(16)
    token_hash = hash_session_token(token)

    import datetime
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    expires = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)).isoformat()
    with closing(sqlite3.connect(DB_PATH)) as con:
        with con:
            con.execute(
                "INSERT INTO cashflow_sessions(session_id, token, game_state, created_at, last_active, token_expires) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, token_hash, json.dumps(engine.persistence_snapshot()), now, now, expires),
            )
    _cashflow_sessions[session_id] = {
        "engine": engine,
        "lock": threading.Lock(),
        "token_hash": token_hash,
    }
    
    return jsonify({
        "status": "started",
        "session_id": session_id,
        "token": token,
        "game": engine.state_snapshot(),
    })


def _get_cashflow_session(session_id: str | None, token: str | None) -> tuple | None:
    """Load and validate a Cashflow game session."""
    if not session_id or not token:
        return None

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "SELECT game_state, token, token_expires FROM cashflow_sessions WHERE session_id = ?",
        (session_id,),
    )
    row = cur.fetchone()
    con.close()
    if not row or not session_token_matches(token, row[1]):
        _cashflow_sessions.pop(session_id, None)
        return None

    import datetime
    try:
        exp = datetime.datetime.fromisoformat(row[2])
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=datetime.timezone.utc)
    except (TypeError, ValueError):
        _cashflow_sessions.pop(session_id, None)
        return None
    if datetime.datetime.now(datetime.timezone.utc) > exp:
        _cashflow_sessions.pop(session_id, None)
        return None

    sess = _cashflow_sessions.get(session_id)
    if sess and sess.get("token_hash") != row[1]:
        _cashflow_sessions.pop(session_id, None)
        return None
    if not sess:
        engine = CashflowGameEngine.from_snapshot(json.loads(row[0]))
        sess = {"engine": engine, "lock": threading.Lock(), "token_hash": row[1]}
        _cashflow_sessions[session_id] = sess
    return sess, session_id


@app.route("/cashflow/turn", methods=["POST"])
def cashflow_turn():
    """Take a turn in the Cashflow game."""
    data = request.get_json(silent=True) or {}
    session_id = request.args.get("session_id") or data.get("session_id")
    token = request.headers.get("X-Session-Token") or data.get("token")
    
    result = _get_cashflow_session(session_id, token)
    if not result:
        return jsonify({"error": "invalid or expired session"}), 401
    
    sess, session_id = result
    engine = sess["engine"]
    lock = sess["lock"]
    
    with lock:
        if engine.player.on_fast_track:
            turn_result = engine.fast_track_turn()
        else:
            turn_result = engine.take_turn()
        _persist_cashflow_state(session_id, engine)
    
    return jsonify({
        "status": "turn_complete",
        "rolled": turn_result.rolled,
        "space": turn_result.space.name,
        "event": turn_result.event,
        "entered_fast_track": turn_result.entered_fast_track,
        "win": turn_result.win,
        "bankrupt": turn_result.bankrupt,
        "game": engine.state_snapshot(),
        "session_id": session_id,
    })


@app.route("/cashflow/deal", methods=["POST"])
def cashflow_deal():
    """Apply a deal card in the Cashflow game."""
    data = request.get_json(silent=True) or {}
    session_id = request.args.get("session_id") or data.get("session_id")
    token = request.headers.get("X-Session-Token") or data.get("token")
    
    result = _get_cashflow_session(session_id, token)
    if not result:
        return jsonify({"error": "invalid or expired session"}), 401
    
    sess, session_id = result
    engine = sess["engine"]
    lock = sess["lock"]
    
    with lock:
        deal_name = data.get("deal_name", "")
        accept = data.get("accept", False)
        
        # Find the deal from the appropriate deck
        card = None
        for deck in [engine.small_deal_deck, engine.big_deal_deck]:
            for c in deck:
                if c.name.lower() == deal_name.lower():
                    card = c
                    break
        
        if not card:
            return jsonify({"error": "deal not found"}), 404
        
        event = engine.apply_deal_card(card, accept)
        _persist_cashflow_state(session_id, engine)
    
    return jsonify({
        "status": "deal_applied",
        "event": event,
        "game": engine.state_snapshot(),
        "session_id": session_id,
    })


@app.route("/cashflow/escape", methods=["POST"])
def cashflow_escape():
    """Enter Fast Track if escape condition is met."""
    data = request.get_json(silent=True) or {}
    session_id = request.args.get("session_id") or data.get("session_id")
    token = request.headers.get("X-Session-Token") or data.get("token")
    
    result = _get_cashflow_session(session_id, token)
    if not result:
        return jsonify({"error": "invalid or expired session"}), 401
    
    sess, session_id = result
    engine = sess["engine"]
    lock = sess["lock"]
    
    with lock:
        event = engine.enter_fast_track()
        _persist_cashflow_state(session_id, engine)
    
    return jsonify({
        "status": "escape_attempted",
        "event": event,
        "on_fast_track": engine.player.on_fast_track,
        "game": engine.state_snapshot(),
        "session_id": session_id,
    })


@app.route("/cashflow/sell", methods=["POST"])
def cashflow_sell():
    """Sell an asset in the Cashflow game."""
    data = request.get_json(silent=True) or {}
    session_id = request.args.get("session_id") or data.get("session_id")
    token = request.headers.get("X-Session-Token") or data.get("token")
    
    result = _get_cashflow_session(session_id, token)
    if not result:
        return jsonify({"error": "invalid or expired session"}), 401
    
    sess, session_id = result
    engine = sess["engine"]
    lock = sess["lock"]
    
    with lock:
        asset_name = data.get("asset_name", "")
        event = engine.sell_asset(asset_name)
        _persist_cashflow_state(session_id, engine)
    
    return jsonify({
        "status": "asset_sold",
        "event": event,
        "game": engine.state_snapshot(),
        "session_id": session_id,
    })


@app.route("/cashflow/decks", methods=["GET"])
def cashflow_decks():
    """Get the Cashflow card decks (for UI reference)."""
    small = [{"name": c.name, "description": c.description, "cost": c.cost} for c in get_indian_small_deals()]
    big = [{"name": c.name, "description": c.description, "cost": c.cost} for c in get_indian_big_deals()]
    doodads = [{"description": c.description, "cost": c.cost} for c in get_indian_doodads()]
    markets = [{"description": c.description, "affects": c.affects} for c in get_indian_markets()]
    
    return jsonify({
        "small_deals": small,
        "big_deals": big,
        "doodads": doodads,
        "markets": markets,
    })


if __name__ == "__main__":
    app.run(port=5000)
