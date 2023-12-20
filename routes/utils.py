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
