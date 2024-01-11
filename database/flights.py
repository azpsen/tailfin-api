import logging
from datetime import datetime
from typing import Dict, Union

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException

from schemas.aircraft import AircraftCreateSchema, aircraft_add_helper, AircraftCategory, AircraftClass
from .aircraft import retrieve_aircraft_by_tail, update_aircraft, update_aircraft_field, retrieve_aircraft
from .db import flight_collection, aircraft_collection
from schemas.flight import FlightConciseSchema, FlightDisplaySchema, FlightCreateSchema, flight_display_helper, \
    flight_add_helper

logger = logging.getLogger("api")


async def retrieve_flights(user: str = "", sort: str = "date", order: int = -1, filter: str = "",
                           filter_val: str = "") -> list[FlightConciseSchema]:
    """
    Retrieve a list of flights, optionally filtered by user

    :param user: User to filter flights by
    :param sort: Parameter to sort results by
    :param order: Sort order
    :param filter: Field to filter flights by
    :param filter_val: Value to filter field by
    :return: List of flights
    """
    filter_options = {}
    if user != "":
        filter_options["user"] = ObjectId(user)
    if filter != "" and filter_val != "":
        fs_keys = list(FlightCreateSchema.__annotations__.keys())
        fs_keys.extend(list(FlightDisplaySchema.__annotations__.keys()))
        if filter not in fs_keys:
            raise HTTPException(400, f"Invalid filter field: {filter}")
        filter_options[filter] = filter_val

    flights = []
    async for flight in flight_collection.find(filter_options).sort({sort: order}):
        flights.append(FlightConciseSchema(**flight_display_helper(flight)))

    return flights


async def retrieve_totals(user: str, start_date: datetime = None, end_date: datetime = None) -> dict:
    """
    Retrieve total times for the given user
    :param user:
    :return:
    """
    match: Dict[str, Union[Dict, ObjectId]] = {"user": ObjectId(user)}

    if start_date is not None:
        match.setdefault("date", {}).setdefault("$gte", start_date)
    if end_date is not None:
        match.setdefault("date", {}).setdefault("$lte", end_date)

    pipeline = [
        {"$match": {"user": ObjectId(user)}},
        {"$lookup": {
            "from": "flight",
            "let": {"aircraft": "$tail_no"},
            "pipeline": [{"$match": {"$expr": {"$eq": ["$$aircraft", "$aircraft"]}}}],
            "as": "flight_data"
        }},
        {"$unwind": "$flight_data"},
        {"$group": {
            "_id": "$aircraft_class",
            "time_total": {"$sum": "$flight_data.time_total"}
        }},
        {"$project": {
            "_id": 0,
            "aircraft_class": "$_id",
            "time_total": 1
        }},
        {"$facet": {
            "by_class": [{"$match": {}}],
            "totals": [
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
                    "xc_dual_recvd": {"$sum": {"$min": ["$time_xc", "$dual_recvd"]}},
                    "xc_solo": {"$sum": {"$min": ["$time_xc", "$time_solo"]}},
                    "xc_pic": {"$sum": {"$min": ["$time_xc", "$time_pic"]}},
                    "night_dual_recvd": {"$sum": {"$min": ["$time_night", "$dual_recvd"]}},
                    "night_pic": {"$sum": {"$min": ["$time_night", "$time_pic"]}}
                }},
                {"$project": {"_id": 0}},
            ]
        }},
        {"$project": {
            "by_class": 1,
            "totals": {"$arrayElemAt": ["$totals", 0]}
        }}
    ]

    cursor = aircraft_collection.aggregate(pipeline)

    result = await cursor.to_list(None)

    if not result:
        return {}

    return dict(result[0])


async def retrieve_flight(id: str) -> FlightDisplaySchema:
    """
    Get detailed information about the given flight

    :param id: ID of flight to retrieve
    :return: Flight information
    """
    flight = await flight_collection.find_one({"_id": ObjectId(id)})

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
    aircraft = await retrieve_aircraft_by_tail(body.aircraft)

    if aircraft is None:
        raise HTTPException(404, "Aircraft not found")

    # Update hobbs of aircraft to reflect new hobbs end
    if body.hobbs_end and body.hobbs_end > 0 and body.hobbs_end != aircraft.hobbs:
        await update_aircraft_field("hobbs", body.hobbs_end, aircraft.id)

    # Insert flight into database
    flight = await flight_collection.insert_one(flight_add_helper(body.model_dump(), id))

    return flight.inserted_id


async def update_flight(body: FlightCreateSchema, id: str) -> str:
    """
    Update given flight in the database

    :param body: Updated flight data
    :param id: ID of flight to update
    :return: ID of updated flight
    """
    flight = await flight_collection.find_one({"_id": ObjectId(id)})

    if flight is None:
        raise HTTPException(404, "Flight not found")

    aircraft = await retrieve_aircraft_by_tail(body.aircraft)

    if aircraft is None:
        raise HTTPException(404, "Aircraft not found")

    # Update hobbs of aircraft to reflect new hobbs end
    if body.hobbs_end > 0 and body.hobbs_end != aircraft.hobbs:
        await update_aircraft_field("hobbs", body.hobbs_end, aircraft.id)

    # Update flight in database
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
