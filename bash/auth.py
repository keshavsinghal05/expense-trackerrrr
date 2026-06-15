import os

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer
from typing import Optional, Dict, Any

# Secret key and settings are configurable via environment variables.
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "1440"))
REMEMBER_ME_REFRESH_EXPIRE_MINUTES = int(os.getenv("REMEMBER_ME_REFRESH_EXPIRE_MINUTES", str(7 * 24 * 60)))
COOKIE_TOKEN_SALT = os.getenv("COOKIE_TOKEN_SALT", "login")
COOKIE_TOKEN_MAX_AGE = int(os.getenv("COOKIE_TOKEN_MAX_AGE", "3600"))

serializer = URLSafeTimedSerializer(SECRET_KEY)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_cookie_token(user_id: int) -> str:
    return serializer.dumps(user_id, salt=COOKIE_TOKEN_SALT)


def decode_cookie_token(token: str) -> Optional[int]:
    try:
        return serializer.loads(token, salt=COOKIE_TOKEN_SALT, max_age=COOKIE_TOKEN_MAX_AGE)
    except Exception:
        return None


# PASSWORD HASHING
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# CREATE JWT TOKEN
def create_access_token(data: Dict[str, Any], expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)

    to_encode.update({"exp": expire, "token_type": "access"})

    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return token


def create_refresh_token(data: Dict[str, Any], expires_minutes: int = REFRESH_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)

    to_encode.update({"exp": expire, "token_type": "refresh"})

    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return token


# VERIFY JWT TOKEN
def verify_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("token_type") != "access":
            return None

        user_id: Optional[int] = payload.get("user_id")
        return user_id

    except JWTError:
        return None


def verify_refresh_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("token_type") != "refresh":
            return None

        user_id: Optional[int] = payload.get("user_id")
        return user_id

    except JWTError:
        return None