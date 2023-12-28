import logging
from typing import Annotated

from fastapi import Depends, APIRouter, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.config import Settings, get_settings
from app.deps import get_current_user_token
from database import tokens, users
from schemas.user import TokenSchema, UserDisplaySchema
from routes.utils import verify_password, create_access_token, create_refresh_token

router = APIRouter()

logger = logging.getLogger("api")


@router.post('/login', summary="Create access and refresh tokens for user", status_code=200, response_model=TokenSchema)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                settings: Annotated[Settings, Depends(get_settings)]) -> TokenSchema:
    """
    Log in as given user - create associated JWT for API access

    :return: JWT for given user
    """
    # Get requested user
    user = await users.get_user_system_info(username=form_data.username)
    if user is None:
        raise HTTPException(401, "Invalid username or password")

    # Verify given password
    hashed_pass = user.password
    if not verify_password(form_data.password, hashed_pass):
        raise HTTPException(401, "Invalid username or password")

    # Create access and refresh tokens
    return TokenSchema(
        access_token=create_access_token(settings, str(user.id)),
        refresh_token=create_refresh_token(settings, str(user.id))
    )


@router.post('/logout', summary="Invalidate current user's token", status_code=200)
async def logout(user_token: (UserDisplaySchema, TokenSchema) = Depends(get_current_user_token)) -> dict:
    """
    Log out given user by adding JWT to a blacklist database

    :return: Logout message
    """
    user, token = user_token

    # Blacklist token
    blacklisted = tokens.blacklist_token(token)

    if not blacklisted:
        logger.debug("Failed to add token to blacklist")
        return {"msg": "Logout failed"}

    return {"msg": "Logout successful"}

# @router.post('/refresh', summary="Refresh JWT token", status_code=200)
# async def refresh(form: OAuth2RefreshRequestForm = Depends()):
#     if request.method == 'POST':
#         form = await request.json()
