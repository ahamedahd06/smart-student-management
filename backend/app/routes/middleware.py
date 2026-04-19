from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import g, request

from app.services.auth_service import decode_token
from app.utils.responses import err


def jwt_required(fn: Callable):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return err("Missing or invalid Authorization header", 401)
        parts = auth.split()
        if len(parts) != 2 or parts[0] != "Bearer":
            return err("Missing or invalid Authorization header", 401)
        payload = decode_token(parts[1].strip())
        if not payload:
            return err("Invalid or expired token", 401)
        g.current_user = payload
        return fn(*args, **kwargs)

    return wrapper


def role_required(*roles: str):
    def deco(fn: Callable):
        @wraps(fn)
        def inner(*args, **kwargs):
            role = g.current_user.get("role")
            if role not in roles:
                return err("Forbidden", 403)
            return fn(*args, **kwargs)

        return inner

    return deco
