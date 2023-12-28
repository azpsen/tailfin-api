import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import ValidationError

from app.deps import get_current_user, admin_required
from database import users as db
from schemas.user import AuthLevel, UserCreateSchema, UserDisplaySchema, UserUpdateSchema
from routes.utils import get_hashed_password

router = APIRouter()

logger = logging.getLogger("api")


@router.post('/', summary="Add user to database", status_code=201, dependencies=[Depends(admin_required)])
async def add_user(body: UserCreateSchema) -> dict:
    """
    Add user to database.

    :return: ID of newly created user
    """

    auth_level = body.level if body.level is not None else AuthLevel.USER

    existing_user = await db.get_user_info(body.username)
    if existing_user is not None:
        logger.info("User %s already exists at auth level %s", existing_user.username, existing_user.level)
        raise HTTPException(400, "Username already exists")

    logger.info("Creating user %s with auth level %s", body.username, auth_level)

    hashed_password = get_hashed_password(body.password)
    user = UserCreateSchema(username=body.username, password=hashed_password, level=auth_level.value)

    added_user = await db.add_user(user)
    if added_user is None:
        raise HTTPException(500, "Failed to add user")

    return {"id": str(added_user)}


@router.delete('/{user_id}', summary="Delete given user and all associated flights", status_code=200,
               dependencies=[Depends(admin_required)])
async def remove_user(user_id: str) -> None:
    """
    Delete given user from database along with all flights associated with said user

    :param user_id: ID of user to delete
    :return: None
    """
    # Delete user from database
    deleted = await db.delete_user(user_id)

    if not deleted:
        logger.info("Attempt to delete nonexistent user %s", user_id)
        raise HTTPException(401, "User does not exist")
    # except ValidationError:
    #     logger.debug("Invalid user delete request")
    #     raise HTTPException(400, "Invalid user")

    # Delete all flights associated with the user TODO
    # Flight.objects(user=user_id).delete()


@router.get('/', summary="Get a list of all users", status_code=200, response_model=list[UserDisplaySchema],
            dependencies=[Depends(admin_required)])
async def get_users() -> list[UserDisplaySchema]:
    """
    Get a list of all users

    :return: List of users in the database
    """
    users = await db.retrieve_users()
    return users


@router.get('/me', status_code=200, response_model=UserDisplaySchema)
async def get_profile(user: UserDisplaySchema = Depends(get_current_user)) -> UserDisplaySchema:
    """
    Return basic user information for the currently logged-in user

    :return: Username and auth level of current user
    """
    return user


@router.get('/{user_id}', status_code=200, dependencies=[Depends(admin_required)], response_model=UserDisplaySchema)
async def get_user_profile(user_id: str) -> UserDisplaySchema:
    """
    Get profile of the given user

    :param user_id: ID of the requested user
    :return: Username and auth level of the requested user
    """
    user = await db.get_user_info_id(id=user_id)

    if user is None:
        logger.warning("User %s not found", user_id)
        raise HTTPException(404, "User not found")

    return user


@router.put('/me', summary="Update the profile of the currently logged-in user", response_model=UserDisplaySchema)
async def update_profile(body: UserUpdateSchema,
                         user: UserDisplaySchema = Depends(get_current_user)) -> UserDisplaySchema:
    """
    Update the profile of the currently logged-in user

    :param body: New information to insert
    :param user: Currently logged-in user
    :return: None
    """
    return await db.edit_profile(user.id, body.username, body.password, body.level)


@router.put('/{user_id}', summary="Update profile of the given user", status_code=200,
            dependencies=[Depends(admin_required)], response_model=UserDisplaySchema)
async def update_user_profile(user_id: str, body: UserUpdateSchema) -> UserDisplaySchema:
    """
    Update the profile of the given user
    :param user_id: ID of the user to update
    :param body: New user information to insert
    :return: Error messages if request is invalid, else 200
    """

    return await db.edit_profile(user_id, body.username, body.password, body.level)
