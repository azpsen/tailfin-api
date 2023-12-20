import logging

from fastapi import APIRouter, HTTPException, Depends

from app.deps import get_current_user, admin_required
from schemas import FlightModel, GetSystemUserSchema

from mongoengine import ValidationError

from database.models import Flight, AuthLevel
from database.utils import get_flight_list

router = APIRouter()

logger = logging.getLogger("flights")


@router.get('/flights', summary="Get flights logged by the currently logged-in user", status_code=200)
async def get_flights(user: GetSystemUserSchema = Depends(get_current_user)) -> list[FlightModel]:
    """
    Get a list of the flights logged by the currently logged-in user

    :return: List of flights
    """
    # l = get_flight_list(filters=[[{"field": "user", "operator": "eq", "value": user.id}]])
    l = get_flight_list(user=str(user.id))
    flights = []
    for f in l:
        flights.append(FlightModel(**f.to_mongo()))
    return [f.to_mongo() for f in flights]


@router.get('/flights/all', summary="Get all flights logged by all users", status_code=200,
            dependencies=[Depends(admin_required)])
def get_all_flights() -> list[FlightModel]:
    """
    Get a list of all flights logged by any user

    :return: List of flights
    """
    flights = [FlightModel(**f.to_mongo()) for f in get_flight_list()]
    return flights


@router.get('/flights/{flight_id}', summary="Get details of a given flight", response_model=FlightModel,
            status_code=200)
def get_flight(flight_id: str, user: GetSystemUserSchema = Depends(get_current_user)):
    """
    Get all details of a given flight

    :param flight_id: ID of requested flight
    :param user: Currently logged-in user
    :return: Flight details
    """
    flight = Flight.objects(id=flight_id).to_json()
    if flight.user != user.id and AuthLevel(user.level) != AuthLevel.ADMIN:
        logger.info("Attempted access to unauthorized flight by %s", user.username)
        raise HTTPException(403, "Unauthorized access")

    return flight


@router.post('/flights', summary="Add a flight logbook entry", status_code=200)
def add_flight(flight_body: FlightModel, user: GetSystemUserSchema = Depends(get_current_user)):
    """
    Add a flight logbook entry

    :param user: Currently logged-in user
    :return: Error message if request invalid, else ID of newly created log
    """
    try:
        flight = Flight(user=user.id, **flight_body.model_dump()).save()
    except ValidationError as e:
        logger.info("Invalid flight body: %s", e)
        raise HTTPException(400, "Invalid request")

    return {"id": flight.id}


@router.put('/flights/{flight_id}', summary="Update the given flight with new information", status_code=201,
            response_model=FlightModel)
def update_flight(flight_id: str, flight_body: FlightModel, user: GetSystemUserSchema = Depends(get_current_user)):
    """
    Update the given flight with new information

    :param flight_id: ID of flight to update
    :param flight_body: New flight information to update with
    :param user: Currently logged-in user
    :return: Updated flight
    """
    flight = Flight.objects(id=flight_id)

    if flight.user != user and AuthLevel(user.level) != AuthLevel.ADMIN:
        logger.info("Attempted access to unauthorized flight by %s", user.username)
        raise HTTPException(403, "Unauthorized access")

    flight.update(**flight_body.model_dump())

    return flight_body


@router.delete('/flights/{flight_id}', summary="Delete the given flight", status_code=200)
def delete_flight(flight_id: str, user: GetSystemUserSchema = Depends(get_current_user)):
    """
    Delete the given flight

    :param flight_id: ID of flight to delete
    :param user: Currently logged-in user
    :return: 200
    """
    flight = Flight.objects(id=flight_id)

    if flight.user != user and AuthLevel(user.level) != AuthLevel.ADMIN:
        logger.info("Attempted access to unauthorized flight by %s", user.username)
        raise HTTPException(403, "Unauthorized access")

    flight.delete()

    return '', 200
