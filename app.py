import json
from datetime import timedelta, datetime, timezone

import bcrypt
from flask import Flask, request, Response, jsonify, session

from database.models import Flight, User, AuthLevel
from mongoengine import connect, ValidationError, DoesNotExist
from flask_jwt_extended import create_access_token, get_jwt , get_jwt_identity, unset_jwt_cookies, jwt_required, JWTManager

api = Flask(__name__)

api.config["JWT_SECRET_KEY"] = "please-remember-to-change-me"
api.config["JWT_ACCESS_TOKEN_EXPORES"] = timedelta(hours=1)
jwt = JWTManager(api)


connect('tailfin')


@api.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            data = response.get_json()
            if type(data) is dict:
                data["access_token"] = access_token
                response.data = json.dumps(data)
        return response
    except (RuntimeError, KeyError):
        # No valid JWT, return original response
        return response


@api.route('/add_user', methods=["POST"])
@jwt_required()
def add_user():
    user = User.objects.get(username=get_jwt_identity())
    if user.level != AuthLevel.ADMIN:
        return '', 401

    username = request.json.get("username", None)
    password = request.json.get("password", None)
    auth_level = request.json.get("auth_level", None)

    try:
        existing_user = User.objects.get(username=username)
        print(existing_user.to_json())
        return jsonify({"msg": "Username already exists"})
    except DoesNotExist:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = User(username=username, password=hashed_password, level=auth_level).save()
        return jsonify({"id": user.id}), 200


@api.route('/users', methods=["GET"])
@jwt_required()
def get_users():
    user = User.objects.get(username=get_jwt_identity())
    if user.level != AuthLevel.ADMIN:
        return '', 401

    users = User.objects.to_json()
    return users, 200


@api.route('/login', methods=["POST"])
def create_token():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    try:
        user = User.objects.get(username=username)
    except DoesNotExist:
        return jsonify({"msg": "Invalid username or password"}), 401
    else:
        if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            access_token = create_access_token(identity=username)
            response = {"access_token": access_token}
            return jsonify(response), 200
        return jsonify({"msg": "Invalid username or password"}), 401


@api.route('/logout', methods=["POST"])
def logout():
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response


@api.route('/profile', methods=["GET"])
@jwt_required()
def get_profile():
    user = User.objects.get(username=get_jwt_identity())
    print(user.to_json())
    return jsonify({"username": user.username, "auth_level:": str(user.level)}), 200


@api.route('/flights', methods=['GET'])
@jwt_required()
def get_flights():
    user = User.objects.get(username=get_jwt_identity()).id
    flights = Flight.objects(user=user).to_json()
    return flights, 200


@api.route('/flights/<flight_id>', methods=['GET'])
@jwt_required()
def get_flight(flight_id):
    user = User.objects.get(username=get_jwt_identity()).id
    flight = Flight.objects(id=flight_id).to_json()
    if flight.user != user:
        return '', 401
    return flight, 200


@api.route('/flights', methods=['POST'])
@jwt_required()
def add_flight():
    user = User.objects(username=get_jwt_identity())

    body = request.get_json()
    try:
        flight = Flight(user=user, **body).save()
    except ValidationError:
        return jsonify({"msg": "Invalid request"})
    id = flight.id
    return jsonify({'id': str(id)}), 201


@api.route('/flights/<flight_id>', methods=['PUT'])
def update_flight(flight_id):
    body = request.get_json()
    Flight.objects(id=flight_id).update(**body)
    return '', 200


@api.route('/flights/<int:index>', methods=['DELETE'])
def delete_flight(index):
    Flight.objects(id=id).delete()
    return '', 200


if __name__ == '__main__':
    if User.objects(level=AuthLevel.ADMIN).count() == 0:
        hashed_password = bcrypt.hashpw("admin".encode('utf-8'), bcrypt.gensalt())
        User(username="admin", password=hashed_password, level=AuthLevel.ADMIN).save()

    api.run()