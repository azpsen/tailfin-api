from datetime import datetime
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError

from app.config import get_settings, Settings
from database.tokens import is_blacklisted
from database.users import get_user_system_info, get_user_system_info_id
from schemas.user import TokenPayload, AuthLevel, UserDisplaySchema

reusable_oath = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    scheme_name="JWT"
)


async def get_current_user(settings: Annotated[Settings, Depends(get_settings)],
                           token: str = Depends(reusable_oath)) -> UserDisplaySchema:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        token_data = TokenPayload(**payload)

        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(401, "Token expired", {"WWW-Authenticate": "Bearer"})
    except (jwt.JWTError, ValidationError):
        raise HTTPException(403, "Could not validate credentials", {"WWW-Authenticate": "Bearer"})

    blacklisted = await is_blacklisted(token)
    if blacklisted:
        raise HTTPException(403, "Token expired", {"WWW-Authenticate": "Bearer"})

    user = await get_user_system_info_id(id=token_data.sub)
    if user is None:
        raise HTTPException(404, "Could not find user")

    return user


async def get_current_user_token(settings: Annotated[Settings, Depends(get_settings)],
                                 token: str = Depends(reusable_oath)) -> (UserDisplaySchema, str):
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        token_data = TokenPayload(**payload)

        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(401, "Token expired", {"WWW-Authenticate": "Bearer"})
    except (jwt.JWTError, ValidationError):
        raise HTTPException(403, "Could not validate credentials", {"WWW-Authenticate": "Bearer"})

    blacklisted = await is_blacklisted(token)
    if blacklisted:
        raise HTTPException(403, "Token expired", {"WWW-Authenticate": "Bearer"})

    user = await get_user_system_info(id=token_data.sub)
    if user is None:
        raise HTTPException(404, "Could not find user")

    return user


async def admin_required(user: Annotated[UserDisplaySchema, Depends(get_current_user)]):
    if user.level < AuthLevel.ADMIN:
        raise HTTPException(403, "Access unauthorized")
