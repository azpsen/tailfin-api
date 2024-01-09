import logging

from bson import ObjectId

from app.config import get_settings
from schemas.aircraft import AircraftCategory, AircraftClass
from .db import user_collection
from routes.utils import get_hashed_password
from schemas.user import AuthLevel, UserCreateSchema

logger = logging.getLogger("api")


def user_helper(user) -> dict:
    """
    Convert given db response into a format usable by UserDisplaySchema

    :param user: Database response
    :return: Usable dict
    """
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "level": user["level"],
    }


def system_user_helper(user) -> dict:
    """
    Convert given db response to a format usable by UserSystemSchema

    :param user: Database response
    :return: Usable dict
    """
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "password": user["password"],
        "level": user["level"],
    }


def create_user_helper(user) -> dict:
    """
    Convert given db response to a format usable by UserCreateSchema

    :param user: Database response
    :return: Usable dict
    """
    return {
        "username": user["username"],
        "password": user["password"],
        "level": user["level"].value,
    }


def flight_display_helper(flight: dict) -> dict:
    """
    Convert given db response to a format usable by FlightDisplaySchema

    :param flight: Database response
    :return: Usable dict
    """
    flight["id"] = str(flight["_id"])
    flight["user"] = str(flight["user"])

    return flight


def flight_add_helper(flight: dict, user: str) -> dict:
    """
    Convert given flight schema and user string to a format that can be inserted into the db

    :param flight: Flight request body
    :param user: User that created flight
    :return: Combined dict that can be inserted into db
    """
    flight["user"] = ObjectId(user)
    return flight


def aircraft_add_helper(aircraft: dict, user: str) -> dict:
    """
    Convert given aircraft dict to a format that can be inserted into the db

    :param aircraft: Aircraft request body
    :param user: User that created aircraft
    :return: Combined dict that can be inserted into db
    """
    aircraft["user"] = ObjectId(user)
    aircraft["aircraft_category"] = aircraft["aircraft_category"].name
    aircraft["aircraft_class"] = aircraft["aircraft_class"].name
    return aircraft


def aircraft_display_helper(aircraft: dict) -> dict:
    """
    Convert given db response into a format usable by AircraftDisplaySchema

    :param aircraft:
    :return: USable dict
    """
    aircraft["id"] = str(aircraft["_id"])
    aircraft["user"] = str(aircraft["user"])
    if aircraft["aircraft_category"] is not AircraftCategory:
        aircraft["aircraft_category"] = AircraftCategory.__members__.get(aircraft["aircraft_category"])
    if aircraft["aircraft_class"] is not AircraftClass:
        aircraft["aircraft_class"] = AircraftClass.__members__.get(aircraft["aircraft_class"])
    return aircraft


# UTILS #

async def create_admin_user():
    """
    Create default admin user if no admin users are present in the database

    :return: None
    """
    if await user_collection.count_documents({"level": AuthLevel.ADMIN.value}) == 0:
        logger.info("No admin users exist. Creating default admin user...")

        settings = get_settings()

        admin_username = settings.tailfin_admin_username
        logger.info("Setting admin username to 'TAILFIN_ADMIN_USERNAME': %s", admin_username)

        admin_password = settings.tailfin_admin_password
        logger.info("Setting admin password to 'TAILFIN_ADMIN_PASSWORD'")

        hashed_password = get_hashed_password(admin_password)
        user = await add_user(
            UserCreateSchema(username=admin_username, password=hashed_password, level=AuthLevel.ADMIN.value))
        logger.info("Default admin user created with username %s", user.username)
