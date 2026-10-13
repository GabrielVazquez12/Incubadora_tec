"""Bounded per-account login attempts for the current single-task deployment."""
from hashlib import sha256
from threading import Lock
from time import monotonic
from fastapi import HTTPException

_attempts = {}
_lock = Lock()
WINDOW = 15 * 60
LIMIT = 60


def login_attempt(email):
    now = monotonic()
    key = sha256(email.encode("utf-8")).digest()
    with _lock:
        if len(_attempts) >= 10000:
            for expired in [entry for entry, (started, _) in _attempts.items() if now - started >= WINDOW]:
                del _attempts[expired]
            if key not in _attempts and len(_attempts) >= 10000:
                raise HTTPException(429, "Demasiados intentos. Inténtalo de nuevo más tarde.", headers={"Retry-After": str(WINDOW)})
        started, count = _attempts.get(key, (now, 0))
        if now - started >= WINDOW:
            started, count = now, 0
        if count >= LIMIT:
            raise HTTPException(429, "Demasiados intentos de inicio de sesión. Inténtalo de nuevo más tarde.", headers={"Retry-After": str(max(1, int(WINDOW - (now - started))))})
        _attempts[key] = (started, count + 1)
