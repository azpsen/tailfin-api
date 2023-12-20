import logging

from fastapi import APIRouter, HTTPException

from models import FlightModel

from mongoengine import DoesNotExist, ValidationError

from flask_jwt_extended import get_jwt_identity, jwt_required

from database.models import User, Flight, AuthLevel
from database.utils import get_flight_list
from routes.utils import auth_level_required

router = APIRouter()

logger = logging.getLogger("flights")


@router.get('/flights')
@jwt_required()
def get_flights():
    """
    Get a list of the flights logged by the currently logged-in user

    :return: List of flights
    """
    try:
        user = User.objects.get(username=get_jwt_identity())
    except DoesNotExist:
        logger.warning("User %s not found", get_jwt_identity())
        return {"msg": "user not found"}, 401

    flights = get_flight_list(filters=[[{"field": "user", "operator": "eq", "value": user.id}]]).to_json()
    return flights, 200


@router.get('/flights/all')
@jwt_required()
@auth_level_required(AuthLevel.ADMIN)
def get_all_flights():
    """
    Get a list of all flights logged by any user

    :return: List of flights
    """
    logger.debug("Get all flights - user: %s", get_jwt_identity())
    flights = get_flight_list().to_json()
    return flights, 200


@router.get('/flights/{flight_id}', response_model=FlightModel)
@jwt_required()
def get_flight(flight_id: str):
    """
    Get all details of a given flight

    :param flight_id: ID of requested flight
    :return: Flight details
    """
    try:
        user = User.objects.get(username=get_jwt_identity())
    except DoesNotExist:
        logger.warning("User %s not found", get_jwt_identity())
        raise HTTPException(401, "User not found")

    flight = Flight.objects(id=flight_id).to_json()
    if flight.user != user.id and AuthLevel(user.level) != AuthLevel.ADMIN:
        logger.info("Attempted access to unauthorized flight by %s", user.username)
        raise HTTPException(403, "Unauthorized access")

    return flight


@router.post('/flights')
@jwt_required()
def add_flight(flight_body: FlightModel):
    """
    Add a flight logbook entry

    :return: Error message if request invalid, else ID of newly created log
    """
    try:
        user = User.objects.get(username=get_jwt_identity())
    except DoesNotExist:
        logger.warning("User %s not found", get_jwt_identity())
        raise HTTPException(401, "User not found")

    try:
        flight = Flight(user=user.id, **flight_body.model_dump()).save()
    except ValidationError as e:
        logger.info("Invalid flight body: %s", e)
        raise HTTPException(400, "Invalid request")

    return {"id": flight.id}


@router.put('/flights/{flight_id}', status_code=201, response_model=FlightModel)
@jwt_required()
def update_flight(flight_id: str, flight_body: FlightModel):
    """
    Update the given flight with new information

    :param flight_id: ID of flight to update
    :param flight_body: New flight information to update with
    :return: Updated flight
    """
    try:
        user = User.objects.get(username=get_jwt_identity())
    except DoesNotExist:
        logger.warning("User %s not found", get_jwt_identity())
        raise HTTPException(status_code=401, detail="user not found")

    flight = Flight.objects(id=flight_id)

    if flight.user != user and AuthLevel(user.level) != AuthLevel.ADMIN:
        logger.info("Attempted access to unauthorized flight by %s", user.username)
        raise HTTPException(403, "Unauthorized access")

    flight.update(**flight_body.model_dump())

    return flight_body


@router.delete('/flights/{flight_id}', status_code=200)
def delete_flight(flight_id: str):
    """
    Delete the given flight

    :param flight_id: ID of flight to delete
    :return: 200
    """
    try:
        user = User.objects.get(username=get_jwt_identity())
    except DoesNotExist:
        logger.warning("User %s not found", get_jwt_identity())
        raise HTTPException(401, "user not found")

    flight = Flight.objects(id=flight_id)

    if flight.user != user and AuthLevel(user.level) != AuthLevel.ADMIN:
        logger.info("Attempted access to unauthorized flight by %s", user.username)
        raise HTTPException(403, "Unauthorized access")

    flight.delete()

    return '', 200
