import logging
from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, HTTPException, Depends, Form, UploadFile, File

from app.deps import get_current_user, admin_required
from database import flights as db
from database.flights import update_flight_fields
from database.img import upload_image

from schemas.flight import FlightConciseSchema, FlightDisplaySchema, FlightCreateSchema, FlightByDateSchema, \
    FlightSchema
from schemas.user import UserDisplaySchema, AuthLevel

router = APIRouter()

logger = logging.getLogger("flights")


@router.get('/', summary="Get flights logged by the currently logged-in user", status_code=200)
async def get_flights(user: UserDisplaySchema = Depends(get_current_user), sort: str = "date", order: int = -1,
                      filter: str = "", filter_val: str = "") -> list[
    FlightConciseSchema]:
    """
    Get a list of the flights logged by the currently logged-in user

    :param user: Current user
    :param sort: Attribute to sort results by
    :param order: Order of sorting (asc/desc)
    :param filter: Field to filter results by
    :param filter_val: Value to filter field by
    :return: List of flights
    """
    flights = await db.retrieve_flights(user.id, sort, order, filter, filter_val)
    return flights


@router.get('/by-date', summary="Get flights logged by the current user, categorized by date", status_code=200,
            response_model=dict)
async def get_flights_by_date(user: UserDisplaySchema = Depends(get_current_user), sort: str = "date",
                              order: int = -1, filter: str = "", filter_val: str = "") -> dict:
    """
    Get a list of the flights logged by the currently logged-in user, categorized by year, month, and day

    :param user: Current user
    :param sort: Attribute to sort results by
    :param order: Order of sorting (asc/desc)
    :param filter: Field to filter results by
    :param filter_val: Value to filter field by
    :return:
    """
    flights = await db.retrieve_flights(user.id, sort, order, filter, filter_val)
    flights_ordered: FlightByDateSchema = {}

    for flight in flights:
        date = flight.date
        flights_ordered.setdefault(date.year, {}).setdefault(date.month, {}).setdefault(date.day, []).append(flight)

    return flights_ordered


@router.get('/totals', summary="Get total statistics for the current user", status_code=200, response_model=dict)
async def get_flight_totals(user: UserDisplaySchema = Depends(get_current_user), start_date: str = "",
                            end_date: str = "") -> dict:
    """
    Get the total statistics for the currently logged-in user

    :param user: Current user
    :param start_date: Only count statistics after this date (optional)
    :param end_date: Only count statistics before this date (optional)
    :return: Dict of totals
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d") if start_date != "" else None
        end = datetime.strptime(end_date, "%Y-%m-%d") if end_date != "" else None
    except (TypeError, ValueError):
        raise HTTPException(400, "Date range not processable")

    return await db.retrieve_totals(user.id, start, end)


@router.get('/all', summary="Get all flights logged by all users", status_code=200,
            dependencies=[Depends(admin_required)], response_model=list[FlightConciseSchema])
async def get_all_flights(sort: str = "date", order: int = -1) -> list[FlightConciseSchema]:
    """
    Get a list of all flights logged by any user

    :param sort: Attribute to sort results by
    :param order: Order of sorting (asc/desc)
    :return: List of flights
    """
    flights = await db.retrieve_flights(sort=sort, order=order)
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
async def add_flight(flight_body: FlightSchema, user: UserDisplaySchema = Depends(get_current_user)) -> dict:
    """
    Add a flight logbook entry

    :param flight_body: Information associated with new flight
    :param images: Images associated with the new flight log
    :param user: Currently logged-in user
    :return: ID of newly created log
    """

    flight_create = FlightCreateSchema(**flight_body.model_dump(), images=[])

    flight = await db.insert_flight(flight_create, user.id)

    return {"id": str(flight)}


@router.post('/{log_id}/add_images', summary="Add images to a flight log")
async def add_images(log_id: str, images: List[UploadFile] = File(...),
                     user: UserDisplaySchema = Depends(get_current_user)):
    """
    Add images to a flight logbook entry

    :param log_id: ID of flight log to add images to
    :param images: Images to add
    :param user: Currently logged-in user
    :return: ID of updated flight
    """
    flight = await db.retrieve_flight(log_id)

    if not str(flight.user) == user.id and not user.level == AuthLevel.ADMIN:
        raise HTTPException(403, "Unauthorized access")

    image_ids = flight.images

    if images:
        for image in images:
            image_response = await upload_image(image, user.id)
            image_ids.append(image_response["file_id"])

    return await update_flight_fields(log_id, dict(images=image_ids))


@router.put('/{flight_id}', summary="Update the given flight with new information", status_code=200)
async def update_flight(flight_id: str, flight_body: FlightCreateSchema,
                        user: UserDisplaySchema = Depends(get_current_user)) -> dict:
    """
    Update the given flight with new information

    :param flight_id: ID of flight to update
    :param flight_body: New flight information to update with
    :param user: Currently logged-in user
    :return: ID of updated flight
    """
    flight = await get_flight(flight_id, user)
    if flight is None:
        raise HTTPException(404, "Flight not found")

    if str(flight.user) != user.id and AuthLevel(user.level) != AuthLevel.ADMIN:
        logger.info("Attempted access to unauthorized flight by %s", user.username)
        raise HTTPException(403, "Unauthorized access")

    updated_flight_id = await db.update_flight(flight_body, flight_id)

    return {"id": str(updated_flight_id)}


@router.patch('/{flight_id}', summary="Update a single field of the given flight with new information", status_code=200)
async def patch_flight(flight_id: str, update: dict,
                       user: UserDisplaySchema = Depends(get_current_user)) -> dict:
    """
    Update a single field of the given flight

    :param flight_id: ID of flight to update
    :param update: Dictionary of fields and values to update
    :param user: Currently logged-in user
    :return: ID of updated flight
    """
    flight = await get_flight(flight_id, user)
    if flight is None:
        raise HTTPException(404, "Flight not found")

    if str(flight.user) != user.id and AuthLevel(user.level) != AuthLevel.ADMIN:
        logger.info("Attempted access to unauthorized flight by %s", user.username)
        raise HTTPException(403, "Unauthorized access")

    updated_flight_id = await db.update_flight_fields(flight_id, update)
    return {"id": str(updated_flight_id)}


@router.delete('/{flight_id}', summary="Delete the given flight", status_code=200, response_model=FlightDisplaySchema)
async def delete_flight(flight_id: str, user: UserDisplaySchema = Depends(get_current_user)) -> FlightDisplaySchema:
    """
    Delete the given flight

    :param flight_id: ID of flight to delete
    :param user: Currently logged-in user
    :return: 200
    """
    flight = await get_flight(flight_id, user)

    if str(flight.user) != user.id and AuthLevel(user.level) != AuthLevel.ADMIN:
        logger.info("Attempted access to unauthorized flight by %s", user.username)
        raise HTTPException(403, "Unauthorized access")

    deleted = await db.delete_flight(flight_id)

    return deleted
