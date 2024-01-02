import logging

from bson import ObjectId
from fastapi import HTTPException

from database.utils import flight_display_helper, flight_add_helper
from .db import flight_collection
from schemas.flight import FlightConciseSchema, FlightDisplaySchema, FlightCreateSchema

logger = logging.getLogger("api")


async def retrieve_flights(user: str = "", sort: str = "date", order: int = -1) -> list[FlightConciseSchema]:
    """
    Retrieve a list of flights, optionally filtered by user

    :param user: User to filter flights by
    :param sort: Parameter to sort results by
    :param order: Sort order
    :return: List of flights
    """
    flights = []
    if user == "":
        async for flight in flight_collection.find().sort({sort: order}):
            flights.append(FlightConciseSchema(**flight_display_helper(flight)))
    else:
        async for flight in flight_collection.find({"user": ObjectId(user)}).sort({sort: order}):
            flights.append(FlightConciseSchema(**flight_display_helper(flight)))
    return flights


async def retrieve_flight(id: str) -> FlightDisplaySchema:
    """
    Get detailed information about the given flight

    :param id: ID of flight to retrieve
    :return: Flight information
    """
    oid = ObjectId(id)
    flight = await flight_collection.find_one({"_id": oid})

    if flight is None:
        raise HTTPException(404, "Flight not found")

    return FlightDisplaySchema(**flight_display_helper(flight))


async def insert_flight(body: FlightCreateSchema, id: str) -> ObjectId:
    """
    Insert a new flight into the database

    :param body: Flight data
    :param id: ID of creating user
    :return: ID of inserted flight
    """
    flight = await flight_collection.insert_one(flight_add_helper(body.model_dump(), id))
    return flight.inserted_id


async def update_flight(body: FlightCreateSchema, id: str) -> FlightDisplaySchema:
    """
    Update given flight in the database

    :param body: Updated flight data
    :param id: ID of flight to update
    :return: ID of updated flight
    """
    flight = await flight_collection.find_one({"_id": ObjectId(id)})

    if flight is None:
        raise HTTPException(404, "Flight not found")

    updated_flight = await flight_collection.update_one({"_id": ObjectId(id)}, {"$set": body})
    return updated_flight.upserted_id


async def delete_flight(id: str) -> FlightDisplaySchema:
    """
    Delete the given flight from the database

    :param id: ID of flight to delete
    :return: Deleted flight information
    """
    flight = await flight_collection.find_one({"_id": ObjectId(id)})

    if flight is None:
        raise HTTPException(404, "Flight not found")

    await flight_collection.delete_one({"_id": ObjectId(id)})
    return FlightDisplaySchema(**flight_display_helper(flight))
