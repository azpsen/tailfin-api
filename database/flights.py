import logging
from datetime import datetime

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


async def retrieve_totals(user: str, start_date: datetime = None, end_date: datetime = None) -> dict:
    """
    Retrieve total times for the given user
    :param user:
    :return:
    """
    match = {"user": ObjectId(user)}

    if start_date is not None:
        match.setdefault("date", {}).setdefault("$gte", start_date)
    if end_date is not None:
        match.setdefault("date", {}).setdefault("$lte", end_date)

    cursor = flight_collection.aggregate([
        {"$match": match},
        {"$group": {
            "_id": None,
            "time_total": {"$sum": "$time_total"},
            "time_solo": {"$sum": "$time_solo"},
            "time_night": {"$sum": "$time_night"},
            "time_pic": {"$sum": "$time_pic"},
            "time_sic": {"$sum": "$time_sic"},
            "time_instrument": {"$sum": "$time_instrument"},
            "time_sim": {"$sum": "$time_sim"},
            "time_xc": {"$sum": "$time_xc"},
            "landings_day": {"$sum": "$landings_day"},
            "landings_night": {"$sum": "$landings_night"},

        }
        },
        {"$project": {"_id": 0}},
    ])

    result = await cursor.to_list(length=None)

    if not result:
        raise HTTPException(404, "No flights found")

    totals = result[0]
    async for log in flight_collection.find({"user": ObjectId(user)}):
        flight = FlightDisplaySchema(**flight_display_helper(log))
        totals["xc_dual_recvd"] = totals.get("xc_dual_recvd", 0) + min(flight.time_xc, flight.dual_recvd)
        totals["xc_solo"] = totals.get("xc_solo", 0) + min(flight.time_xc, flight.time_solo)
        totals["xc_pic"] = totals.get("xc_pic", 0) + min(flight.time_xc, flight.time_pic)
        totals["night_dual_recvd"] = totals.get("night_dual_recvd", 0) + min(flight.time_night,
                                                                             flight.dual_recvd)
        totals["night_pic"] = totals.get("night_pic", 0) + min(flight.time_night, flight.time_pic)

    return totals


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

    updated_flight = await flight_collection.update_one({"_id": ObjectId(id)}, {"$set": body.model_dump()})
    if updated_flight is None:
        raise HTTPException(500, "Failed to update flight")

    return id


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
