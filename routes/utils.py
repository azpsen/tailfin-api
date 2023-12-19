import os

import bcrypt
from flask import current_app

from flask_jwt_extended import get_jwt_identity

from database.models import AuthLevel, User


def auth_level_required(level: AuthLevel):
    """
    Limit access to given authorization level.

    :param level: Required authorization level to access this endpoint
    :return: 403 Unauthorized upon auth failure or response of decorated function on auth success
    """

    def auth_inner(func):
        def auth_wrapper(*args, **kwargs):
            user = User.objects.get(username=get_jwt_identity())
            if AuthLevel(user.level) < level:
                current_app.logger.warning("Attempted access to unauthorized resource by %s", user.username)
                return '', 403
            else:
                return func(*args, **kwargs)

        auth_wrapper.__name__ = func.__name__
        return auth_wrapper

    return auth_inner


def create_admin_user():
    """
    Create default admin user if no admin users are present in the database

    :return: None
    """
    if User.objects(level=AuthLevel.ADMIN.value).count() == 0:
        current_app.logger.info("No admin users exist. Creating default admin user...")
        try:
            admin_username = os.environ["TAILFIN_ADMIN_USERNAME"]
            current_app.logger.info("Setting admin username to 'TAILFIN_ADMIN_USERNAME': %s", admin_username)
        except KeyError:
            admin_username = "admin"
            current_app.logger.info("'TAILFIN_ADMIN_USERNAME' not set, using default username 'admin'")
        try:
            admin_password = os.environ["TAILFIN_ADMIN_PASSWORD"]
            current_app.logger.info("Setting admin password to 'TAILFIN_ADMIN_PASSWORD'")
        except KeyError:
            admin_password = "admin"
            current_app.logger.warning("'TAILFIN_ADMIN_PASSWORD' not set, using default password 'admin'\n"
                               "Change this as soon as possible")
        hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
        User(username=admin_username, password=hashed_password, level=AuthLevel.ADMIN.value).save()
        current_app.logger.info("Default admin user created with username %s", User.objects.get(level=AuthLevel.ADMIN).username)
