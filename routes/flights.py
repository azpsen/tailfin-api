from flask import Blueprint, current_app, request, jsonify
from mongoengine import DoesNotExist, ValidationError

from flask_jwt_extended import get_jwt_identity, jwt_required

from database.models import User, Flight, AuthLevel
from routes.utils import auth_level_required

flights_api = Blueprint('flights_api', __name__)


@flights_api.route('/flights', methods=['GET'])
@jwt_required()
def get_flights():
    """
    Get a list of the flights logged by the currently logged-in user

    :return: List of flights
    """
    try:
        user = User.objects.get(username=get_jwt_identity())
    except DoesNotExist:
        current_app.logger.warning("User %s not found", get_jwt_identity())
        return {"msg": "user not found"}, 401
    flights = Flight.objects(user=user.id).to_json()
    return flights, 200


@flights_api.route('/flights/all', methods=['GET'])
@jwt_required()
@auth_level_required(AuthLevel.ADMIN)
def get_all_flights():
    """
    Get a list of all flights logged by any user

    :return: List of flights
    """
    flights = Flight.objects.to_json()
    return flights, 200


@flights_api.route('/flights/<flight_id>', methods=['GET'])
@jwt_required()
def get_flight(flight_id):
    """
    Get all details of a given flight

    :param flight_id: ID of requested flight
    :return: Flight details
    """
    try:
        user = User.objects.get(username=get_jwt_identity())
    except DoesNotExist:
        current_app.logger.warning("User %s not found", get_jwt_identity())
        return {"msg": "user not found"}, 401

    flight = Flight.objects(id=flight_id).to_json()
    if flight.user != user.id and AuthLevel(user.level) != AuthLevel.ADMIN:
        current_app.logger.warning("Attempted access to unauthorized flight by %s", user.username)
        return {"msg": "Unauthorized access"}, 403
    return flight, 200


@flights_api.route('/flights', methods=['POST'])
@jwt_required()
def add_flight():
    """
    Add a flight logbook entry

    :return: Error message if request invalid, else ID of newly created log
    """
    try:
        user = User.objects.get(username=get_jwt_identity())
    except DoesNotExist:
        current_app.logger.warning("User %s not found", get_jwt_identity())
        return {"msg": "user not found"}, 401

    body = request.get_json()
    try:
        flight = Flight(user=user, **body).save()
    except ValidationError:
        return jsonify({"msg": "Invalid request"})
    id = flight.id
    return jsonify({'id': str(id)}), 201


@flights_api.route('/flights/<flight_id>', methods=['PUT'])
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
        current_app.logger.warning("User %s not found", get_jwt_identity())
        return {"msg": "user not found"}, 401

    flight = Flight.objects(id=flight_id)

    if flight.user != user and AuthLevel(user.level) != AuthLevel.ADMIN:
        current_app.logger.warning("Attempted access to unauthorized flight by %s", user.username)
        return {"msg": "Unauthorized access"}, 403

    body = request.get_json()
    flight.update(**body)

    return '', 200


@flights_api.route('/flights/<flight_id>', methods=['DELETE'])
def delete_flight(flight_id):
    """
    Delete the given flight

    :param flight_id: ID of flight to delete
    :return: Error messages if user not found or access unauthorized, else 200
    """
    try:
        user = User.objects.get(username=get_jwt_identity())
    except DoesNotExist:
        current_app.logger.warning("User %s not found", get_jwt_identity())
        return {"msg": "user not found"}, 401

    flight = Flight.objects(id=flight_id)

    if flight.user != user and AuthLevel(user.level) != AuthLevel.ADMIN:
        current_app.logger.warning("Attempted access to unauthorized flight by %s", user.username)
        return {"msg": "Unauthorized access"}, 403

    flight.delete()

    return '', 200
