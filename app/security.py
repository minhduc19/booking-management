import hashlib
import hmac
import secrets


PBKDF2_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    """Return a salted PBKDF2-SHA256 password hash suitable for storage."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS
    ).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"


def verify_password(password: str, encoded_hash: str) -> bool:
    """Verify a password against a hash produced by :func:`hash_password`."""
    try:
        algorithm, iterations, salt, expected_digest = encoded_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), int(iterations)
        ).hex()
    except (AttributeError, TypeError, ValueError):
        return False
    return hmac.compare_digest(digest, expected_digest)
