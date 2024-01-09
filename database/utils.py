import logging

from app.config import get_settings
from .db import user_collection
from routes.utils import get_hashed_password
from schemas.user import AuthLevel, UserCreateSchema
from .users import add_user

logger = logging.getLogger("api")


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

        if user is None:
            raise Exception("Failed to create default admin user")

        logger.info("Default admin user created with username %s", admin_username)
