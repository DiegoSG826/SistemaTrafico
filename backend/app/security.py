from datetime import timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerificationError
from fastapi import HTTPException

from .database import utcnow

hasher = PasswordHasher()


def verify(password, stored):
    try:
        return hasher.verify(stored, password)
    except (VerificationError, InvalidHash):
        return False


def token_for(user, secret):
    return jwt.encode({"sub": str(user.id), "exp": utcnow()+timedelta(hours=1),
                       "iat": utcnow(), "iss": "sgt-cdmx", "aud": "sgt-api"},
                      secret, algorithm="HS256")


def decode(token, secret):
    try:
        return int(jwt.decode(token, secret, algorithms=["HS256"],
                              issuer="sgt-cdmx", audience="sgt-api")["sub"])
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise HTTPException(401, "Sesión inválida o vencida", headers={"WWW-Authenticate": "Bearer"})
