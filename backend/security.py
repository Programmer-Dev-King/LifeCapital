import hashlib
import hmac
import secrets


_PASSWORD_SCHEME = "pbkdf2_sha256"
_PASSWORD_ITERATIONS = 600_000
_LEGACY_PASSWORD_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    if not isinstance(password, str) or not password:
        raise ValueError("password must be a non-empty string")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PASSWORD_ITERATIONS)
    return f"{_PASSWORD_SCHEME}${_PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str, legacy_salt: str | None = None) -> bool:
    if not isinstance(password, str) or not password or not isinstance(encoded, str) or not encoded:
        return False

    parts = encoded.split("$")
    if len(parts) == 4 and parts[0] == _PASSWORD_SCHEME:
        try:
            iterations = int(parts[1])
            salt = bytes.fromhex(parts[2])
            expected = bytes.fromhex(parts[3])
        except ValueError:
            return False
        if not 100_000 <= iterations <= _PASSWORD_ITERATIONS or len(salt) != 16 or len(expected) != 32:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)

    if legacy_salt:
        legacy = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), legacy_salt.encode("utf-8"), _LEGACY_PASSWORD_ITERATIONS
        ).hex()
        return hmac.compare_digest(legacy, encoded)
    return False


def password_needs_rehash(encoded: str) -> bool:
    if not isinstance(encoded, str) or not encoded:
        return True
    parts = encoded.split("$")
    if len(parts) != 4 or parts[0] != _PASSWORD_SCHEME:
        return True
    try:
        iterations = int(parts[1])
    except ValueError:
        return True
    return iterations < _PASSWORD_ITERATIONS


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def session_token_matches(token: str | None, stored_hash: str | None) -> bool:
    if not isinstance(token, str) or not token or not isinstance(stored_hash, str) or not stored_hash:
        return False
    return hmac.compare_digest(hash_session_token(token), stored_hash)
