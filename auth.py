"""
auth.py
Password hashing for customer accounts.

Uses PBKDF2-HMAC-SHA256 (stdlib `hashlib`, no external dependency) with a
random per-user salt and 100,000 iterations. Plain-text passwords are
never stored -- only the salt and the resulting hash.
"""

import hashlib
import os

_ITERATIONS = 100_000


def hash_password(password: str, salt: bytes = None):
    """Return (salt_hex, hash_hex). Generates a new random salt if none given."""
    if salt is None:
        salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return salt.hex(), pwd_hash.hex()


def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    """Re-hash the supplied password with the stored salt and compare."""
    salt = bytes.fromhex(salt_hex)
    _, computed_hash = hash_password(password, salt)
    return computed_hash == hash_hex
