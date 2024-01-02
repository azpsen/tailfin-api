import logging

from fastapi import APIRouter, HTTPException, Depends

from app.deps import get_current_user, admin_required
from database import flights as db
from schemas.flight import FlightConciseSchema, FlightDisplaySchema, FlightCreateSchema

from schemas.user import UserDisplaySchema, AuthLevel

router = APIRouter()

logger = logging.getLogger("flights")


@router.get('/', summary="Get flights logged by the currently logged-in user", status_code=200,
            response_model=list[FlightConciseSchema])
async def get_flights(user: UserDisplaySchema = Depends(get_current_user), sort: str = "date", order: int = -1) -> list[
    FlightConciseSchema]:
    """
    Get a list of the flights logged by the currently logged-in user

    :return: List of flights
    """
    # l = get_flight_list(filters=[[{"field": "user", "operator": "eq", "value": user.id}]])
    flights = await db.retrieve_flights(user.id, sort, order)
    return flights


@router.get('/all', summary="Get all flights logged by all users", status_code=200,
            dependencies=[Depends(admin_required)], response_model=list[FlightConciseSchema])
async def get_all_flights(sort: str = "date", order: int = -1) -> list[FlightConciseSchema]:
    """
    Get a list of all flights logged by any user

    :return: List of flights
    """
    flights = await db.retrieve_flights(sort, order)
    return flights


@router.get('/{flight_id}', summary="Get details of a given flight", response_model=FlightDisplaySchema,
            status_code=200)
async def get_flight(flight_id: str, user: UserDisplaySchema = Depends(get_current_user)) -> FlightDisplaySchema:
    """
    Get all details of a given flight

    :param flight_id: ID of requested flight
    :param user: Currently logged-in user
    :return: Flight details
    """
    flight = await db.retrieve_flight(flight_id)
    if str(flight.user) != user.id and AuthLevel(user.level) != AuthLevel.ADMIN:
        logger.info("Attempted access to unauthorized flight by %s", user.username)
        raise HTTPException(403, "Unauthorized access")

    return flight


@router.post('/', summary="Add a flight logbook entry", status_code=200)
async def add_flight(flight_body: FlightCreateSchema, user: UserDisplaySchema = Depends(get_current_user)) -> dict:
    """
    Add a flight logbook entry

    :param flight_body: Information associated with new flight
    :param user: Currently logged-in user
    :return: Error message if request invalid, else ID of newly created log
    """

    flight = await db.insert_flight(flight_body, user.id)

    return {"id": str(flight)}


@router.put('/{flight_id}', summary="Update the given flight with new information", status_code=201)
async def update_flight(flight_id: str, flight_body: FlightCreateSchema,
                        user: UserDisplaySchema = Depends(get_current_user)) -> str:
    """
    Update the given flight with new information

    :param flight_id: ID of flight to update
    :param flight_body: New flight information to update with
    :param user: Currently logged-in user
    :return: Updated flight
    """
    flight = await get_flight(flight_id)
    if flight is None:
        raise HTTPException(404, "Flight not found")

    if flight.user != user and AuthLevel(user.level) != AuthLevel.ADMIN:
        logger.info("Attempted access to unauthorized flight by %s", user.username)
        raise HTTPException(403, "Unauthorized access")

    updated_flight_id = await db.update_flight(flight_body, flight_id)

    return str(updated_flight_id)


@router.delete('/{flight_id}', summary="Delete the given flight", status_code=200, response_model=FlightDisplaySchema)
async def delete_flight(flight_id: str, user: UserDisplaySchema = Depends(get_current_user)) -> FlightDisplaySchema:
    """
    Delete the given flight

    :param flight_id: ID of flight to delete
    :param user: Currently logged-in user
    :return: 200
    """
    flight = await get_flight(flight_id)

    if flight.user != user and AuthLevel(user.level) != AuthLevel.ADMIN:
        logger.info("Attempted access to unauthorized flight by %s", user.username)
        raise HTTPException(403, "Unauthorized access")

    deleted = await db.delete_flight(flight_id)

    return deleted
