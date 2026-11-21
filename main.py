import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-dev-key-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(
    title="FastAPI JWT Auth",
    description="Регистрация, вход и защита маршрутов с помощью PyJWT",
    version="1.0.0",
)

security = HTTPBearer()


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Хранилище пользователей в памяти
users_db: dict[str, dict] = {}
next_id: int = 1


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": username,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> dict:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Невалидный или просроченный токен",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Срок действия токена истек",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credentials_exception

    user = users_db.get(username)
    if user is None:
        raise credentials_exception
    return user


@app.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister) -> UserOut:
    global next_id
    if payload.username in users_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким username уже существует",
        )
    if any(u["email"] == payload.email for u in users_db.values()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует",
        )

    user_record = {
        "id": next_id,
        "username": payload.username,
        "email": payload.email,
        "hashed_password": hash_password(payload.password),
    }
    next_id += 1
    users_db[payload.username] = user_record

    return UserOut(
        id=user_record["id"],
        username=user_record["username"],
        email=user_record["email"],
    )


@app.post("/login", response_model=TokenResponse)
def login(payload: UserLogin) -> TokenResponse:
    user = users_db.get(payload.username)
    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )

    token = create_access_token(username=user["username"])
    return TokenResponse(access_token=token)


@app.get("/users/me", response_model=UserOut)
def read_current_user(current_user: Annotated[dict, Depends(get_current_user)]) -> UserOut:
    return UserOut(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
    )


@app.get("/protected")
def protected_route(current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
    return {
        "message": f"Добро пожаловать, {current_user['username']}! Доступ к защищенному маршруту разрешен."
    }
