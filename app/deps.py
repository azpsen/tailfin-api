from datetime import datetime
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from mongoengine import DoesNotExist
from pydantic import ValidationError

from app.config import get_settings, Settings
from database.models import User, TokenBlacklist
from schemas import GetSystemUserSchema, TokenPayload, AuthLevel

reusable_oath = OAuth2PasswordBearer(
    tokenUrl="/login",
    scheme_name="JWT"
)


async def get_current_user(settings: Annotated[Settings, Depends(get_settings)],
                           token: str = Depends(reusable_oath)) -> GetSystemUserSchema:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        token_data = TokenPayload(**payload)

        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(401, "Token expired", {"WWW-Authenticate": "Bearer"})
    except (jwt.JWTError, ValidationError):
        raise HTTPException(403, "Could not validate credentials", {"WWW-Authenticate": "Bearer"})

    try:
        TokenBlacklist.objects.get(token=token)
        raise HTTPException(403, "Token expired", {"WWW-Authenticate": "Bearer"})
    except DoesNotExist:
        try:
            user = User.objects.get(id=token_data.sub)
        except DoesNotExist:
            raise HTTPException(404, "Could not find user")

        return GetSystemUserSchema(id=str(user.id), username=user.username, level=user.level, password=user.password)


async def get_current_user_token(settings: Annotated[Settings, Depends(get_settings)],
                                 token: str = Depends(reusable_oath)) -> (GetSystemUserSchema, str):
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        token_data = TokenPayload(**payload)

        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(401, "Token expired", {"WWW-Authenticate": "Bearer"})
    except (jwt.JWTError, ValidationError):
        raise HTTPException(403, "Could not validate credentials", {"WWW-Authenticate": "Bearer"})

    try:
        TokenBlacklist.objects.get(token=token)
        raise HTTPException(403, "Token expired", {"WWW-Authenticate": "Bearer"})
    except DoesNotExist:
        try:
            user = User.objects.get(id=token_data.sub)
        except DoesNotExist:
            raise HTTPException(404, "Could not find user")

        return GetSystemUserSchema(id=str(user.id), username=user.username, level=user.level,
                                   password=user.password), token


async def admin_required(user: Annotated[GetSystemUserSchema, Depends(get_current_user)]):
    if user.level < AuthLevel.ADMIN:
        raise HTTPException(403, "Access unauthorized")
