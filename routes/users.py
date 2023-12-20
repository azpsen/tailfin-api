from typing import Annotated

import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm

from mongoengine import DoesNotExist, ValidationError

from app.deps import get_current_user, admin_required, reusable_oath, get_current_user_token
from app.config import Settings, get_settings
from database.models import AuthLevel, User, Flight, TokenBlacklist
from schemas import CreateUserSchema, TokenSchema, GetSystemUserSchema, GetUserSchema, UpdateUserSchema
from utils import get_hashed_password, verify_password, create_access_token, create_refresh_token
from database.utils import edit_profile

router = APIRouter()

logger = logging.getLogger("users")


@router.post('/users', summary="Add user to database", status_code=201, dependencies=[Depends(admin_required)])
async def add_user(body: CreateUserSchema) -> dict:
    """
    Add user to database.

    :return: ID of newly created user
    """

    auth_level = body.level if body.level is not None else AuthLevel.USER

    try:
        existing_user = User.objects.get(username=body.username)
        logger.info("User %s already exists at auth level %s", existing_user.username, existing_user.level)
        raise HTTPException(400, "Username already exists")

    except DoesNotExist:
        logger.info("Creating user %s with auth level %s", body.username, auth_level)

        hashed_password = get_hashed_password(body.password)
        user = User(username=body.username, password=hashed_password, level=auth_level.value)

        try:
            user.save()
        except ValidationError:
            raise HTTPException(400, "Invalid request")

        return {"id": str(user.id)}


@router.delete('/users/{user_id}', summary="Delete given user and all associated flights", status_code=200,
               dependencies=[Depends(admin_required)])
async def remove_user(user_id: str) -> None:
    """
    Delete given user from database along with all flights associated with said user

    :param user_id: ID of user to delete
    :return: None
    """
    try:
        # Delete user from database
        User.objects.get(id=user_id).delete()
    except DoesNotExist:
        logger.info("Attempt to delete nonexistent user %s", user_id)
        raise HTTPException(401, "User does not exist")
    except ValidationError:
        logger.debug("Invalid user delete request")
        raise HTTPException(400, "Invalid user")

    # Delete all flights associated with the user
    Flight.objects(user=user_id).delete()


@router.get('/users', summary="Get a list of all users", status_code=200, response_model=list[GetUserSchema],
            dependencies=[Depends(admin_required)])
async def get_users() -> list[GetUserSchema]:
    """
    Get a list of all users

    :return: List of users in the database
    """
    users = User.objects.all()
    return [GetUserSchema(id=str(u.id), username=u.username, level=u.level) for u in users]


@router.post('/login', summary="Create access and refresh tokens for user", status_code=200, response_model=TokenSchema)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                settings: Annotated[Settings, Depends(get_settings)]) -> TokenSchema:
    """
    Log in as given user - create associated JWT for API access

    :return: JWT for given user
    """

    try:
        user = User.objects.get(username=form_data.username)
        hashed_pass = user.password
        if not verify_password(form_data.password, hashed_pass):
            raise HTTPException(401, "Invalid username or password")
        return TokenSchema(
            access_token=create_access_token(settings, str(user.id)),
            refresh_token=create_refresh_token(settings, str(user.id))
        )
    except DoesNotExist:
        raise HTTPException(401, "Invalid username or password")


@router.post('/logout', summary="Invalidate current user's token", status_code=200)
async def logout(user_token: (GetSystemUserSchema, TokenSchema) = Depends(get_current_user_token)) -> dict:
    """
    Log out given user by adding JWT to a blacklist database

    :return: Logout message
    """
    user, token = user_token
    print(token)
    try:
        TokenBlacklist(token=str(token)).save()
    except ValidationError:
        logger.debug("Failed to add token to blacklist")

    return {"msg": "Logout successful"}


# @router.post('/refresh', summary="Refresh JWT token", status_code=200)
# async def refresh(form: OAuth2RefreshRequestForm = Depends()):
#     if request.method == 'POST':
#         form = await request.json()


@router.get('/profile', status_code=200, response_model=GetUserSchema)
async def get_profile(user: GetSystemUserSchema = Depends(get_current_user)) -> GetUserSchema:
    """
    Return basic user information for the currently logged-in user

    :return: Username and auth level of current user
    """
    return user


@router.get('/profile/{user_id}', status_code=200, dependencies=[Depends(admin_required)], response_model=GetUserSchema)
async def get_user_profile(user_id: str) -> GetUserSchema:
    """
    Get profile of the given user

    :param user_id: ID of the requested user
    :return: Username and auth level of the requested user
    """
    try:
        user = User.objects.get(id=user_id)
    except DoesNotExist:
        logger.warning("User %s not found", user_id)
        raise HTTPException(404, "User not found")

    return GetUserSchema(id=str(user.id), username=user.username, level=user.level)


@router.put('/profile', summary="Update the profile of the currently logged-in user", response_model=GetUserSchema)
async def update_profile(body: UpdateUserSchema,
                         user: GetSystemUserSchema = Depends(get_current_user)) -> GetUserSchema:
    """
    Update the profile of the currently logged-in user

    :param body: New information to insert
    :param user: Currently logged-in user
    :return: None
    """
    return await edit_profile(user.id, body.username, body.password, body.level)


@router.put('/profile/{user_id}', summary="Update profile of the given user", status_code=200,
            dependencies=[Depends(admin_required)], response_model=GetUserSchema)
async def update_user_profile(user_id: str, body: UpdateUserSchema) -> GetUserSchema:
    """
    Update the profile of the given user
    :param user_id: ID of the user to update
    :param body: New user information to insert
    :return: Error messages if request is invalid, else 200
    """

    return await edit_profile(user_id, body.username, body.password, body.level)
