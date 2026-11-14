"""Admin CLI for SQLite-backed users and sessions."""
import getpass
import sqlite3
import sys
import os
from pathlib import Path

from backend.security import hash_password


DB_PATH = os.environ.get(
    "LIFECAP_DB_PATH",
    str(Path(__file__).resolve().parent.parent / "lifecycle_sessions.db"),
)


def list_sessions():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT session_id, created_at, last_active FROM sessions")
    rows = cur.fetchall()
    con.close()
    print("session_id\tcreated_at\tlast_active")
    for s in rows:
        print(f"{s[0]}\t{s[1]}\t{s[2]}")


def list_users():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT username FROM users")
    rows = cur.fetchall()
    con.close()
    for r in rows:
        print(r[0])


def create_user(username: str, password: str):
    if not username.strip():
        raise ValueError("username must not be empty")
    if len(password) < 12:
        raise ValueError("password must be at least 12 characters")
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO users(username, pw_hash) VALUES (?, ?) "
        "ON CONFLICT(username) DO UPDATE SET pw_hash = excluded.pw_hash",
        (username, hash_password(password)),
    )
    con.commit()
    con.close()
    print(f"Created user {username}")


def expire_session(session_id: str):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    cur.execute("DELETE FROM cashflow_sessions WHERE session_id = ?", (session_id,))
    con.commit()
    con.close()
    print(f"Expired session {session_id}")


def expire_all():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    sessions = cur.execute("DELETE FROM sessions").rowcount
    cashflow_sessions = cur.execute("DELETE FROM cashflow_sessions").rowcount
    con.commit()
    con.close()
    print(f"Expired {sessions} simulator sessions and {cashflow_sessions} Cashflow sessions")


def expire_old(ttl_seconds: int):
    import datetime

    cutoff = (
        datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        - datetime.timedelta(seconds=ttl_seconds)
    ).isoformat()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT session_id FROM sessions WHERE last_active < ?", (cutoff,))
    rows = cur.fetchall()
    ids = [r[0] for r in rows]
    cur.execute("DELETE FROM sessions WHERE last_active < ?", (cutoff,))
    cur.execute("DELETE FROM cashflow_sessions WHERE last_active < ?", (cutoff,))
    cashflow_count = cur.rowcount
    con.commit()
    con.close()
    print(f"Expired {len(ids)} simulator sessions and {cashflow_count} Cashflow sessions older than {ttl_seconds} seconds")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python backend/admin.py list|list_users|expire <session_id>|expire_all|expire_old <seconds>|create_user <username>")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == 'list':
        list_sessions()
    elif cmd == 'list_users':
        list_users()
    elif cmd == 'expire' and len(sys.argv) == 3:
        expire_session(sys.argv[2])
    elif cmd == 'expire_old' and len(sys.argv) == 3:
        try:
            ttl = int(sys.argv[2])
        except Exception:
            print('ttl must be integer seconds')
            sys.exit(2)
        expire_old(ttl)
    elif cmd == 'expire_all' and len(sys.argv) == 2:
        expire_all()
    elif cmd == 'create_user' and len(sys.argv) == 3:
        password = getpass.getpass("Password (12+ characters): ")
        confirmation = getpass.getpass("Confirm password: ")
        if password != confirmation:
            print("Passwords do not match")
            sys.exit(2)
        try:
            create_user(sys.argv[2], password)
        except ValueError as exc:
            print(str(exc))
            sys.exit(2)
    else:
        print("Unknown command")
