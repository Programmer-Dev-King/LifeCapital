import hashlib
import unittest

from backend.security import hash_password, hash_session_token, password_needs_rehash, session_token_matches, verify_password


class SecurityTests(unittest.TestCase):
    def test_password_hashes_use_unique_salts_and_verify(self):
        password = "correct horse battery"
        first = hash_password(password)
        second = hash_password(password)

        self.assertNotEqual(first, second)
        self.assertTrue(verify_password(password, first))
        self.assertFalse(verify_password("incorrect", first))
        self.assertFalse(password_needs_rehash(first))

    def test_legacy_passwords_require_explicit_salt_and_need_rehash(self):
        password = "legacy-password"
        salt = "old-operator-salt"
        legacy = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()

        self.assertFalse(verify_password(password, legacy))
        self.assertTrue(verify_password(password, legacy, salt))
        self.assertTrue(password_needs_rehash(legacy))

    def test_session_tokens_are_compared_as_hashes(self):
        token = "random-session-token"
        token_hash = hash_session_token(token)

        self.assertNotEqual(token, token_hash)
        self.assertTrue(session_token_matches(token, token_hash))
        self.assertFalse(session_token_matches("wrong-token", token_hash))
        self.assertFalse(session_token_matches(None, token_hash))


if __name__ == "__main__":
    unittest.main()
