import os
import secrets
import hashlib
from modules.db_handling import Database
from fastapi import APIRouter, Depends, HTTPException, Header

router = APIRouter(prefix="/auth", tags=["Auth"])
db = Database()

_tokens: dict[str, int] = {}


def _hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    return salt + ":" + hashlib.sha256((salt + password).encode()).hexdigest()


def _verify_password(password: str, stored: str) -> bool:
    salt, pw_hash = stored.split(":", 1)
    return pw_hash == hashlib.sha256((salt + password).encode()).hexdigest()


async def get_current_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization[7:]
    user_id = _tokens.get(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_optional_user(authorization: str = Header(None)) -> dict | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    user_id = _tokens.get(token)
    if user_id is None:
        return None
    return db.get_user_by_id(user_id)
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization[7:]
    user_id = _tokens.get(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/register")
async def register(data: dict):
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        raise HTTPException(status_code=400, detail="username, email, and password are required")

    if db.get_user_by_username(username):
        raise HTTPException(status_code=409, detail="Username already taken")

    if db.get_user_by_email(email):
        raise HTTPException(status_code=409, detail="Email already registered")

    user_id = db.create_user(username, email, _hash_password(password))
    return {"id": user_id, "username": username, "email": email}


@router.post("/login")
async def login(data: dict):
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password are required")

    user = db.get_user_by_username(username)
    if not user or not _verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = secrets.token_hex(32)
    _tokens[token] = user["id"]

    return {
        "token": token,
        "user": {"id": user["id"], "username": user["username"], "email": user["email"]},
    }


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {"id": user["id"], "username": user["username"], "email": user["email"]}


@router.post("/logout")
async def logout(user: dict = Depends(get_current_user),
                 authorization: str = Header(None)):
    token = authorization[7:]
    _tokens.pop(token, None)
    return {"message": "Logged out"}
