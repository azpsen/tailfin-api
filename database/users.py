import logging

from bson import ObjectId
from fastapi import HTTPException

from .db import user_collection, flight_collection
from routes.utils import get_hashed_password
from schemas.user import UserDisplaySchema, UserCreateSchema, UserSystemSchema, AuthLevel, user_helper, \
    create_user_helper, system_user_helper

logger = logging.getLogger("api")


async def retrieve_users() -> list[UserDisplaySchema]:
    """
    Retrieve a list of all users in the database

    :return: List of users
    """
    users = []
    async for user in user_collection.find():
        users.append(UserDisplaySchema(**user_helper(user)))
    return users


async def add_user(user_data: UserCreateSchema) -> ObjectId:
    """
    Add a user to the database

    :param user_data: User data to insert into database
    :return: ID of inserted user
    """
    user = await user_collection.insert_one(create_user_helper(user_data.model_dump()))
    return user.inserted_id


async def get_user_info_id(id: str) -> UserDisplaySchema:
    """
    Get user information from given user ID

    :param id: ID of user to retrieve
    :return: User information
    """
    user = await user_collection.find_one({"_id": ObjectId(id)})
    if user:
        return UserDisplaySchema(**user_helper(user))


async def get_user_info(username: str) -> UserDisplaySchema:
    """
    Get user information from given username

    :param username: Username of user to retrieve
    :return: User information
    """
    user = await user_collection.find_one({"username": username})
    if user:
        return UserDisplaySchema(**user_helper(user))


async def get_user_system_info_id(id: str) -> UserSystemSchema:
    """
    Get user information and password hash from given ID

    :param id: ID of user to retrieve
    :return: User information and password
    """
    user = await user_collection.find_one({"_id": ObjectId(id)})
    if user:
        return UserSystemSchema(**system_user_helper(user))


async def get_user_system_info(username: str) -> UserSystemSchema:
    """
    Get user information and password hash from given username

    :param username: Username of user to retrieve
    :return: User information and password
    """
    user = await user_collection.find_one({"username": username})
    if user:
        return UserSystemSchema(**system_user_helper(user))


async def delete_user(id: str) -> UserDisplaySchema:
    """
    Delete given user and all associated flights from the database

    :param id: ID of user to delete
    :return: Information of deleted user
    """
    user = await user_collection.find_one({"_id": ObjectId(id)})

    if user is None:
        raise HTTPException(404, "User not found")

    await user_collection.delete_one({"_id": ObjectId(id)})

    # Delete all flights associated with user
    await flight_collection.delete_many({"user": ObjectId(id)})

    return UserDisplaySchema(**user_helper(user))


async def edit_profile(user_id: str, username: str = None, password: str = None,
                       auth_level: AuthLevel = None) -> UserDisplaySchema:
    """
    Update the profile of the given user

    :param user_id: ID of user to update
    :param username: New username
    :param password: New password
    :param auth_level: New authorization level
    :return: Error message if user not found or access unauthorized, else 200
    """
    user = await get_user_info_id(user_id)
    if user is None:
        raise HTTPException(404, "User not found")

    if username:
        existing_users = await user_collection.count_documents({"username": username})
        if existing_users > 0:
            raise HTTPException(400, "Username not available")
    if auth_level:
        if auth_level is not AuthLevel(user.level) and AuthLevel(user.level) < AuthLevel.ADMIN:
            logger.info("Unauthorized attempt by %s to change auth level", user.username)
            raise HTTPException(403, "Unauthorized attempt to change auth level")

    if username:
        user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"username": username}})
    if password:
        hashed_password = get_hashed_password(password)
        user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"password": hashed_password}})
    if auth_level:
        user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"level": auth_level}})

    updated_user = await get_user_info_id(user_id)
    return updated_user
