import bcrypt

import logging
from fastapi import APIRouter, HTTPException

from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, unset_jwt_cookies, jwt_required, \
    JWTManager
from mongoengine import DoesNotExist, ValidationError

from database.models import AuthLevel, User, Flight
from models import UserModel
from routes.utils import auth_level_required

router = APIRouter()

logger = logging.getLogger("users")


@router.post('/users', status_code=201)
@jwt_required()
@auth_level_required(AuthLevel.ADMIN)
def add_user(body: UserModel):
    """
    Add user to database.

    :return: Failure message if user already exists, otherwise ID of newly created user
    """

    auth_level = body.level if body.level is not None else AuthLevel.USER

    try:
        existing_user = User.objects.get(username=body.username)
        logger.debug("User %s already exists at auth level %s", existing_user.username, existing_user.level)
        return {"msg": "Username already exists"}

    except DoesNotExist:
        logger.info("Creating user %s with auth level %s", body.username, auth_level)

        hashed_password = bcrypt.hashpw(body.password.encode('utf-8'), bcrypt.gensalt())
        user = User(username=body.username, password=hashed_password, level=auth_level)

        try:
            user.save()
        except ValidationError:
            raise HTTPException(400, "Invalid request")

        return {"id": str(user.id)}


@router.delete('/users/{user_id}', status_code=200)
@jwt_required()
@auth_level_required(AuthLevel.ADMIN)
def remove_user(user_id: str):
    """
    Delete given user from database along with all flights associated with said user

    :param user_id: ID of user to delete
    :return: None
    """
    try:
        # Delete user from database
        User.objects.get(id=user_id).delete()
    except DoesNotExist:
        logger.info("Attempt to delete nonexistent user %s by %s", user_id, get_jwt_identity())
        raise HTTPException(401, "User does not exist")

    # Delete all flights associated with the user
    Flight.objects(user=user_id).delete()


@router.get('/users', status_code=200, response_model=list[UserModel])
@jwt_required()
@auth_level_required(AuthLevel.ADMIN)
def get_users():
    """
    Get a list of all users

    :return: List of users in the database
    """
    users = User.objects.to_json()
    return users


@router.post('/login', status_code=200)
def create_token(body: UserModel):
    """
    Log in as given user - create associated JWT for API access

    :return: JWT for given user
    """

    try:
        user = User.objects.get(username=body.username)
    except DoesNotExist:
        raise HTTPException(401, "Invalid username or password")
    else:
        if bcrypt.checkpw(body.password.encode('utf-8'), user.password.encode('utf-8')):
            access_token = create_access_token(identity=body.username)
            logger.info("%s successfully logged in", body.username)
            return {"access_token": access_token}

        logger.info("Failed login attempt for user %s", body.username)
        raise HTTPException(401, "Invalid username or password")


@router.post('/logout', status_code=200)
def logout():
    """
    Log out given user. Note that JWTs cannot be natively revoked so this must also be handled by the frontend

    :return: Message with JWT removed from headers
    """
    response = {"msg": "logout successful"}
    # unset_jwt_cookies(response)
    return response


@router.get('/profile/{user_id}', status_code=200)
@jwt_required()
@auth_level_required(AuthLevel.ADMIN)
def get_user_profile(user_id: str):
    """
    Get profile of the given user

    :param user_id: ID of the requested user
    :return: Username and auth level of the requested user
    """
    try:
        user = User.objects.get(id=user_id)
    except DoesNotExist:
        logger.warning("User %s not found", get_jwt_identity())
        raise HTTPException(401, "User not found")

    return {"username": user.username, "auth_level:": str(user.level)}


@router.put('/profile/{user_id}', status_code=200)
@jwt_required()
@auth_level_required(AuthLevel.ADMIN)
def update_user_profile(user_id: str, body: UserModel):
    """
    Update the profile of the given user
    :param user_id: ID of the user to update
    :param body: New user information to insert
    :return: Error messages if request is invalid, else 200
    """
    try:
        user = User.objects.get(id=user_id)
    except DoesNotExist:
        logger.warning("User %s not found", get_jwt_identity())
        raise HTTPException(401, "User not found")

    return update_profile(user.id, body.username, body.password, body.level)


@router.get('/profile', status_code=200)
@jwt_required()
def get_profile():
    """
    Return basic user information for the currently logged-in user

    :return: Username and auth level of current user
    """
    try:
        user = User.objects.get(username=get_jwt_identity())
    except DoesNotExist:
        logger.warning("User %s not found", get_jwt_identity())
        raise HTTPException(401, "User not found")

    return {"username": user.username, "auth_level:": str(user.level)}


@router.put('/profile')
@jwt_required()
def update_profile(body: UserModel):
    """
    Update the profile of the currently logged-in user

    :param body: New information to insert
    :return: None
    """
    try:
        user = User.objects.get(username=get_jwt_identity())
    except DoesNotExist:
        logger.warning("User %s not found", get_jwt_identity())
        raise HTTPException(401, "User not found")

    return update_profile(user.id, body["username"], body["password"], body["auth_level"])
