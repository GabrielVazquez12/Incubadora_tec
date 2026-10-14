"""Bounded per-account login attempts for the current single-task deployment."""
from hashlib import sha256
from threading import Lock
from time import monotonic
from fastapi import HTTPException

_attempts = {}
_lock = Lock()
WINDOW = 15 * 60
LIMIT = 60
_public_attempts = {}


def public_attempt(namespace, address):
    """Bound anonymous contact writes without retaining raw IP addresses."""
    now = monotonic()
    key = sha256(f'{namespace}:{address}'.encode()).digest()
    with _lock:
        if len(_public_attempts) >= 10000:
            for expired in [entry for entry, (started, _) in _public_attempts.items() if now - started >= 60]:
                del _public_attempts[expired]
            if key not in _public_attempts and len(_public_attempts) >= 10000:
                raise HTTPException(429, 'Demasiadas solicitudes. Inténtalo más tarde.', headers={'Retry-After': '60'})
        started, count = _public_attempts.get(key, (now, 0))
        if now - started >= 60:
            started, count = now, 0
        if count >= 30:
            raise HTTPException(429, 'Demasiados mensajes. Inténtalo en un minuto.', headers={'Retry-After': str(max(1, int(60 - (now - started))))})
        _public_attempts[key] = (started, count + 1)


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
