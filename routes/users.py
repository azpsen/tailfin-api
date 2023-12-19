import bcrypt
from flask import Blueprint, request, jsonify, current_app

from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, unset_jwt_cookies, jwt_required, \
    JWTManager
from mongoengine import DoesNotExist, ValidationError

from database.models import AuthLevel, User, Flight
from routes.utils import auth_level_required

users_api = Blueprint('users_api', __name__)


@users_api.route('/users', methods=["POST"])
@jwt_required()
@auth_level_required(AuthLevel.ADMIN)
def add_user():
    """
    Add user to database.

    :return: Failure message if user already exists, otherwise ID of newly created user
    """
    body = request.get_json()
    try:
        username = body["username"]
        password = body["password"]
    except KeyError:
        return jsonify({"msg": "Missing username or password"})
    try:
        auth_level = AuthLevel(body["auth_level"])
    except KeyError:
        auth_level = AuthLevel.USER

    try:
        existing_user = User.objects.get(username=username)
        current_app.logger.info("User %s already exists at auth level %s", existing_user.username, existing_user.level)
        return jsonify({"msg": "Username already exists"})
    except DoesNotExist:
        current_app.logger.info("Creating user %s with auth level %s", username, auth_level)

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = User(username=username, password=hashed_password, level=auth_level.value)
        try:
            user.save()
        except ValidationError:
            return jsonify({"msg": "Invalid request"})

        return jsonify({"id": str(user.id)}), 201


@users_api.route('/users/<user_id>', methods=['DELETE'])
@jwt_required()
@auth_level_required(AuthLevel.ADMIN)
def remove_user(user_id):
    """
    Delete given user from database

    :param user_id: ID of user to delete
    :return: 200 if success, 401 if user does not exist
    """
    try:
        User.objects.get(id=user_id).delete()
    except DoesNotExist:
        current_app.logger.info("Attempt to delete nonexistent user %s by %s", user_id, get_jwt_identity())
        return {"msg": "User does not exist"}, 401
    Flight.objects(user=user_id).delete()
    return '', 200


@users_api.route('/users', methods=["GET"])
@jwt_required()
@auth_level_required(AuthLevel.ADMIN)
def get_users():
    """
    Get a list of all users

    :return: List of users in the database
    """
    users = User.objects.to_json()
    return users, 200


@users_api.route('/login', methods=["POST"])
def create_token():
    """
    Log in as given user and return JWT for API access

    :return: 401 if username or password invalid, else JWT
    """
    body = request.get_json()
    try:
        username = body["username"]
        password = body["password"]
    except KeyError:
        return jsonify({"msg": "Missing username or password"})

    try:
        user = User.objects.get(username=username)
    except DoesNotExist:
        return jsonify({"msg": "Invalid username or password"}), 401
    else:
        if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            access_token = create_access_token(identity=username)
            current_app.logger.info("%s successfully logged in", username)
            response = {"access_token": access_token}
            return jsonify(response), 200
        current_app.logger.info("Failed login attempt from %s", request.remote_addr)
        return jsonify({"msg": "Invalid username or password"}), 401


@users_api.route('/logout', methods=["POST"])
def logout():
    """
    Log out given user. Note that JWTs cannot be natively revoked so this must also be handled by the frontend

    :return: Message with JWT removed from headers
    """
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response


@users_api.route('/profile/<user_id>', methods=["GET"])
@jwt_required()
@auth_level_required(AuthLevel.ADMIN)
def get_user_profile(user_id):
    """
    Get profile of the given user

    :param user_id: ID of the requested user
    :return: 401 is user does not exist, else username and auth level
    """
    try:
        user = User.objects.get(id=user_id)
    except DoesNotExist:
        current_app.logger.warning("User %s not found", get_jwt_identity())
        return {"msg": "User not found"}, 401
    return jsonify({"username": user.username, "auth_level:": str(user.level)}), 200


@users_api.route('/profile/<user_id>', methods=["PUT"])
@jwt_required()
@auth_level_required(AuthLevel.ADMIN)
def update_user_profile(user_id):
    """
    Update the profile of the given user
    :param user_id: ID of the user to update
    :return: Error messages if request is invalid, else 200
    """
    try:
        user = User.objects.get(id=user_id)
    except DoesNotExist:
        current_app.logger.warning("User %s not found", get_jwt_identity())
        return jsonify({"msg": "User not found"}), 401

    body = request.get_json()
    return update_profile(user.id, body["username"], body["password"], body["auth_level"])


@users_api.route('/profile', methods=["GET"])
@jwt_required()
def get_profile():
    """
    Return basic user information for the currently logged-in user

    :return: 401 if user not found, else username and auth level
    """
    try:
        user = User.objects.get(username=get_jwt_identity())
    except DoesNotExist:
        current_app.logger.warning("User %s not found", get_jwt_identity())
        return jsonify({"msg": "User not found"}), 401
    return jsonify({"username": user.username, "auth_level:": str(user.level)}), 200


@users_api.route('/profile', methods=["PUT"])
@jwt_required()
def update_profile():
    """
    Update the profile of the currently logged-in user

    :return: Error messages if request is invalid, else 200
    """
    try:
        user = User.objects.get(username=get_jwt_identity())
    except DoesNotExist:
        current_app.logger.warning("User %s not found", get_jwt_identity())
        return {"msg": "user not found"}, 401
    body = request.get_json()

    return update_profile(user.id, body["username"], body["password"], body["auth_level"])
