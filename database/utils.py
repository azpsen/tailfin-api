import bcrypt
from flask import jsonify, current_app
from mongoengine import DoesNotExist

from database.models import User, AuthLevel


def update_profile(user_id, username=None, password=None, auth_level=None):
    """
    Update the profile of the given user

    :param user_id: ID of user to update
    :param username: New username
    :param password: New password
    :param auth_level: New authorization level
    :return: Error message if user not found or access unauthorized, else 200
    """
    try:
        user = User.objects.get(id=user_id)
    except DoesNotExist:
        return {"msg": "user not found"}, 401

    if username:
        existing_users = User.objects(username=username).count()
        if existing_users != 0:
            return jsonify({"msg": "Username not available"})
    if password:
        hashed_password = bcrypt.hashpw(password.encode('UTF-8'), bcrypt.gensalt())
    if auth_level:
        if AuthLevel(user.level) < AuthLevel.ADMIN:
            current_app.logger.warning("Unauthorized attempt by %s to change auth level", user.username)
            return jsonify({"msg": "Unauthorized attempt to change auth level"}), 403

    if username:
        user.update_one(username=username)
    if password:
        user.update_one(password=password)
    if auth_level:
        user.update_one(level=auth_level)

    return '', 200
