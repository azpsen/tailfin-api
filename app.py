import functools
import json, os, sys
from datetime import timedelta, datetime, timezone

import bcrypt
from flask import Flask, request, Response, jsonify, session
from pymongo import database

from database.models import Flight, User, AuthLevel
from mongoengine import connect, ValidationError, DoesNotExist
from flask_jwt_extended import create_access_token, get_jwt , get_jwt_identity, unset_jwt_cookies, jwt_required, JWTManager

# Initialize Flask app
api = Flask(__name__)

# Set JWT key from environment variable
try:
    api.config["JWT_SECRET_KEY"] = os.environ["TAILFIN_DB_KEY"]
except KeyError:
    api.logger.error("Please set 'TAILFIN_DB_KEY' environment variable")
    exit(1)

# Set JWT keys to expire after 1 hour
api.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

# Initialize JWT manager
jwt = JWTManager(api)

# Connect to MongoDB
connect('tailfin')


def auth_level_required(level: AuthLevel):
    """
    Limit access to given authorization level.

    :param level: required authorization level to access this endpoint
    :return: 403 Unauthorized upon auth failure or response of decorated function on auth success
    """
    def auth_inner(func):
        def auth_wrapper(*args, **kwargs):
            user = User.objects.get(username=get_jwt_identity())
            if AuthLevel(user.level) < level:
                api.logger.warning("Attempted access to unauthorized resource by %s", user.username)
                return '', 403
            else:
                return func(*args, **kwargs)
        auth_wrapper.__name__ = func.__name__
        return auth_wrapper
    return auth_inner


@api.after_request
def refresh_expiring_jwts(response):
    """
    Refresh/reissue JWTs that are near expiry following each request containing a JWT

    :param response: Response given by previous request
    :return: Original response with refreshed JWT
    """
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            api.logger.info("Refreshing expiring JWT")
            access_token = create_access_token(identity=get_jwt_identity())
            data = response.get_json()
            if type(data) is dict:
                data["access_token"] = access_token
                response.data = json.dumps(data)
        return response
    except (RuntimeError, KeyError):
        # No valid JWT, return original response
        api.logger.info("No valid JWT, cannot refresh expiry")
        return response


@api.route('/users', methods=["POST"])
@jwt_required()
@auth_level_required(AuthLevel.ADMIN)
def add_user():
    """
    Add user to database.

    :return: Failure message if user already exists, otherwise ID of newly created user
    """
    body = request.get_json()
    username = body.username
    password = body.password
    auth_level = AuthLevel(body.auth_level)

    try:
        existing_user = User.objects.get(username=username)
        api.logger.info("User %s already exists at auth level %s", existing_user.username, existing_user.level)
        return jsonify({"msg": "Username already exists"})
    except DoesNotExist:
        api.logger.info("Creating user %s with auth level %s", username, auth_level)

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = User(username=username, password=hashed_password, level=auth_level.value)
        user.save()

        return jsonify({"id": user.id}), 201


@api.route('/users/<user_id>', methods=['DELETE'])
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
        api.logger.info("Attempt to delete nonexistent user %s by %s", user_id, get_jwt_identity())
        return {"msg": "User does not exist"}, 401
    Flight.objects(user=user_id).delete()
    return '', 200


@api.route('/users', methods=["GET"])
@jwt_required()
@auth_level_required(AuthLevel.ADMIN)
def get_users():
    """
    Get a list of all users

    :return: List of users in the database
    """
    users = User.objects.to_json()
    return users, 200


@api.route('/login', methods=["POST"])
def create_token():
    """
    Log in as given user and return JWT for API access

    :return: 401 if username or password invalid, else JWT
    """
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    try:
        user = User.objects.get(username=username)
    except DoesNotExist:
        return jsonify({"msg": "Invalid username or password"}), 401
    else:
        if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            access_token = create_access_token(identity=username)
            api.logger.info("%s successfully logged in", username)
            response = {"access_token": access_token}
            return jsonify(response), 200
        api.logger.info("Failed login attempt from %s", request.remote_addr)
        return jsonify({"msg": "Invalid username or password"}), 401


@api.route('/logout', methods=["POST"])
def logout():
    """
    Log out given user. Note that JWTs cannot be natively revoked so this must also be handled by the frontend

    :return: Message with JWT removed from headers
    """
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response


@api.route('/profile/<user_id>', methods=["GET"])
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
        api.logger.warning("User %s not found", get_jwt_identity())
        return {"msg": "User not found"}, 401
    return jsonify({"username": user.username, "auth_level:": str(user.level)}), 200


@api.route('/profile/<user_id>', methods=["PUT"])
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
        api.logger.warning("User %s not found", get_jwt_identity())
        return jsonify({"msg": "User not found"}), 401

    body = request.get_json()
    return update_profile(user.id, body.username, body.password, body.auth_level)


@api.route('/profile', methods=["GET"])
@jwt_required()
def get_profile():
    """
    Return basic user information for the currently logged-in user

    :return: 401 if user not found, else username and auth level
    """
    try:
        user = User.objects.get(username=get_jwt_identity())
    except DoesNotExist:
        api.logger.warning("User %s not found", get_jwt_identity())
        return jsonify({"msg": "User not found"}), 401
    return jsonify({"username": user.username, "auth_level:": str(user.level)}), 200


@api.route('/profile', methods=["PUT"])
@jwt_required()
def update_profile():
    """
    Update the profile of the currently logged-in user

    :return: Error messages if request is invalid, else 200
    """
    try:
        user = User.objects.get(username=get_jwt_identity())
    except DoesNotExist:
        api.logger.warning("User %s not found", get_jwt_identity())
        return {"msg": "user not found"}, 401
    body = request.get_json()

    return update_profile(user.id, body.username, body.password, body.auth_level)


@api.route('/flights', methods=['GET'])
@jwt_required()
def get_flights():
    """
    Get a list of the flights logged by the currently logged-in user

    :return: List of flights
    """
    user = User.objects.get(username=get_jwt_identity()).id
    flights = Flight.objects(user=user).to_json()
    return flights, 200


@api.route('/flights/all', methods=['GET'])
@jwt_required()
@auth_level_required(AuthLevel.ADMIN)
def get_all_flights():
    """
    Get a list of all flights logged by any user

    :return: List of flights
    """
    flights = Flight.objects.to_json()
    return flights, 200


@api.route('/flights/<flight_id>', methods=['GET'])
@jwt_required()
def get_flight(flight_id):
    """
    Get all details of a given flight

    :param flight_id: ID of requested flight
    :return: Flight details
    """
    user = User.objects.get(username=get_jwt_identity()).id
    flight = Flight.objects(id=flight_id).to_json()
    if flight.user != user and AuthLevel(user.level) != AuthLevel.ADMIN:
        api.logger.warning("Attempted access to unauthorized flight by %s", user.username)
        return {"msg": "Unauthorized access"}, 403
    return flight, 200


@api.route('/flights', methods=['POST'])
@jwt_required()
def add_flight():
    """
    Add a flight logbook entry

    :return: Error message if request invalid, else ID of newly created log
    """
    user = User.objects(username=get_jwt_identity())

    body = request.get_json()
    try:
        flight = Flight(user=user, **body).save()
    except ValidationError:
        return jsonify({"msg": "Invalid request"})
    id = flight.id
    return jsonify({'id': str(id)}), 201


@api.route('/flights/<flight_id>', methods=['PUT'])
@jwt_required()
def update_flight(flight_id):
    """
    Update the given flight with new information

    :param flight_id: ID of flight to update
    :return: Error messages if user not found or access unauthorized, else 200
    """
    try:
        user = User.objects.get(username=get_jwt_identity())
    except DoesNotExist:
        api.logger.warning("User %s not found", get_jwt_identity())
        return {"msg": "user not found"}, 401

    flight = Flight.objects(id=flight_id)

    if flight.user != user and AuthLevel(user.level) != AuthLevel.ADMIN:
        api.logger.warning("Attempted access to unauthorized flight by %s", user.username)
        return {"msg": "Unauthorized access"}, 403

    body = request.get_json()
    flight.update(**body)

    return '', 200


@api.route('/flights/<flight_id>', methods=['DELETE'])
def delete_flight(flight_id):
    """
    Delete the given flight

    :param flight_id: ID of flight to delete
    :return: Error messages if user not found or access unauthorized, else 200
    """
    try:
        user = User.objects.get(username=get_jwt_identity())
    except DoesNotExist:
        api.logger.warning("User %s not found", get_jwt_identity())
        return {"msg": "user not found"}, 401

    flight = Flight.objects(id=flight_id)

    if flight.user != user and AuthLevel(user.level) != AuthLevel.ADMIN:
        api.logger.warning("Attempted access to unauthorized flight by %s", user.username)
        return {"msg": "Unauthorized access"}, 403

    flight.delete()

    return '', 200


if __name__ == '__main__':
    # Create default admin user if no admin users found
    if User.objects(level=AuthLevel.ADMIN.value).count() == 0:
        api.logger.info("No admin users exist. Creating default admin user...")
        try:
            admin_username = os.environ["TAILFIN_ADMIN_USERNAME"]
            api.logger.info("Setting admin username to 'TAILFIN_ADMIN_USERNAME': %s", admin_username)
        except KeyError:
            admin_username = "admin"
            api.logger.info("'TAILFIN_ADMIN_USERNAME' not set, using default username 'admin'")
        try:
            admin_password = os.environ["TAILFIN_ADMIN_PASSWORD"]
            api.logger.info("Setting admin password to 'TAILFIN_ADMIN_PASSWORD'")
        except KeyError:
            admin_password = "admin"
            api.logger.warning("'TAILFIN_ADMIN_PASSWORD' not set, using default password 'admin'\n"
                               "Change this as soon as possible")
        hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
        User(username=admin_username, password=hashed_password, level=AuthLevel.ADMIN).save()
        api.logger.info("Default admin user created with username %s", User.objects.get(level=AuthLevel.ADMIN).username)

    # Start the app
    api.run()
