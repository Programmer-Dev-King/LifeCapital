"""Admin CLI for session management (SQLite-backed).

Usage:
    python backend/admin.py list
    python backend/admin.py expire <session_id>
"""
import sqlite3
import sys
import os

DB_PATH = os.path.join(os.getcwd(), "lifecycle_sessions.db")


def list_sessions():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT session_id, token, created_at, last_active FROM sessions")
    rows = cur.fetchall()
    con.close()
    print("session_id\ttoken\tcreated_at\tlast_active")
    for s in rows:
        print(f"{s[0]}\t{s[1]}\t{s[2]}\t{s[3]}")


def list_users():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT username FROM users")
    rows = cur.fetchall()
    con.close()
    for r in rows:
        print(r[0])


def create_user(username: str, password: str):
    import hashlib, os

    salt = os.environ.get("LIFECAP_SALT", "static_salt_please_change").encode("utf-8")
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    pw_hash = dk.hex()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("INSERT OR REPLACE INTO users(username, pw_hash) VALUES (?, ?)", (username, pw_hash))
    con.commit()
    con.close()
    print(f"Created user {username}")


def expire_session(session_id: str):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    con.commit()
    con.close()
    print(f"Expired session {session_id}")


def expire_old(ttl_seconds: int):
    import datetime

    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(seconds=ttl_seconds)).isoformat()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT session_id FROM sessions WHERE last_active < ?", (cutoff,))
    rows = cur.fetchall()
    ids = [r[0] for r in rows]
    for sid in ids:
        cur.execute("DELETE FROM sessions WHERE session_id = ?", (sid,))
    con.commit()
    con.close()
    print(f"Expired {len(ids)} sessions older than {ttl_seconds} seconds")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python backend/admin.py list|expire <session_id>")
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
    elif cmd == 'create_user' and len(sys.argv) == 4:
        create_user(sys.argv[2], sys.argv[3])
    else:
        print("Unknown command")
