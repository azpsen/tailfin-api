import logging
from datetime import datetime
from typing import Dict, Union

from bson import ObjectId

from utils import to_objectid
from fastapi import HTTPException
from pydantic import ValidationError

from schemas.aircraft import aircraft_class_dict, aircraft_category_dict
from .aircraft import retrieve_aircraft_by_tail, update_aircraft_field
from .db import flight_collection, aircraft_collection
from schemas.flight import FlightConciseSchema, FlightDisplaySchema, FlightCreateSchema, flight_display_helper, \
    flight_add_helper, FlightPatchSchema

logger = logging.getLogger("api")

fs_keys = list(FlightPatchSchema.__annotations__.keys()) + list(FlightDisplaySchema.__annotations__.keys())


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
        filter_options["user"] = to_objectid(user)
    if filter != "" and filter_val != "":
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
    match: Dict[str, Union[Dict, ObjectId]] = {"user": to_objectid(user)}

    if start_date is not None:
        match.setdefault("date", {}).setdefault("$gte", start_date)
    if end_date is not None:
        match.setdefault("date", {}).setdefault("$lte", end_date)

    by_class_pipeline = [
        {"$match": {"user": to_objectid(user)}},
        {"$lookup": {
            "from": "flight",
            "let": {"aircraft": "$tail_no"},
            "pipeline": [
                {"$match": {
                    "$expr": {
                        "$eq": ["$$aircraft", "$aircraft"]
                    }
                }}
            ],
            "as": "flight_data"
        }},
        {"$unwind": "$flight_data"},
        {"$group": {
            "_id": {
                "aircraft_category": "$aircraft_category",
                "aircraft_class": "$aircraft_class"
            },
            "time_total": {
                "$sum": "$flight_data.time_total"
            },
        }},
        {"$group": {
            "_id": "$_id.aircraft_category",
            "classes": {
                "$push": {
                    "aircraft_class": "$_id.aircraft_class",
                    "time_total": "$time_total",
                }
            },
        }},
        {"$project": {
            "_id": 0,
            "aircraft_category": "$_id",
            "classes": 1,
        }},
    ]

    class_cursor = aircraft_collection.aggregate(by_class_pipeline)
    by_class_list = await class_cursor.to_list(None)

    totals_pipeline = [
        {"$match": {"user": to_objectid(user)}},
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

    totals_cursor = flight_collection.aggregate(totals_pipeline)
    totals_list = await totals_cursor.to_list(None)

    if not totals_list and not by_class_list:
        return {}

    totals_dict = dict(totals_list[0])

    for entry in by_class_list:
        entry["aircraft_category"] = aircraft_category_dict[entry["aircraft_category"]]
        for cls in entry["classes"]:
            cls["aircraft_class"] = aircraft_class_dict[cls["aircraft_class"]]

    result = {
        "by_class": by_class_list,
        "totals": totals_dict
    }

    return result


async def retrieve_flight(id: str) -> FlightDisplaySchema:
    """
    Get detailed information about the given flight

    :param id: ID of flight to retrieve
    :return: Flight information
    """
    flight = await flight_collection.find_one({"_id": to_objectid(id)})

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
    flight = await flight_collection.find_one({"_id": to_objectid(id)})

    if flight is None:
        raise HTTPException(404, "Flight not found")

    aircraft = await retrieve_aircraft_by_tail(body.aircraft)

    if aircraft is None:
        raise HTTPException(404, "Aircraft not found")

    # Update hobbs of aircraft to reflect new hobbs end
    if body.hobbs_end and body.hobbs_end and 0 < aircraft.hobbs != body.hobbs_end:
        await update_aircraft_field("hobbs", body.hobbs_end, aircraft.id)

    # Update flight in database
    updated_flight = await flight_collection.update_one({"_id": to_objectid(id)}, {"$set": body.model_dump()})

    if updated_flight is None:
        raise HTTPException(500, "Failed to update flight")

    return id


async def update_flight_fields(id: str, update: dict) -> str:
    """
    Update a single field of the given flight in the database

    :param id: ID of flight to update
    :param update: Dictionary of fields and values to update
    :return: ID of updated flight
    """
    print(fs_keys)
    for field in update.keys():
        if field not in fs_keys:
            raise HTTPException(400, f"Invalid update field: {field}")

    flight = await flight_collection.find_one({"_id": to_objectid(id)})

    if flight is None:
        raise HTTPException(404, "Flight not found")

    try:
        parsed_update = FlightPatchSchema.model_validate(update)
    except ValidationError as e:
        raise HTTPException(422, e.errors())

    update_dict = {field: value for field, value in parsed_update.model_dump().items() if field in update.keys()}

    if "aircraft" in update_dict.keys():
        aircraft = await retrieve_aircraft_by_tail(update_dict["aircraft"])

        if aircraft is None:
            raise HTTPException(404, "Aircraft not found")

    updated_flight = await flight_collection.update_one({"_id": to_objectid(id)}, {"$set": update_dict})

    if updated_flight is None:
        raise HTTPException(500, "Failed to update flight")

    return id


async def delete_flight(id: str) -> FlightDisplaySchema:
    """
    Delete the given flight from the database

    :param id: ID of flight to delete
    :return: Deleted flight information
    """
    flight = await flight_collection.find_one({"_id": to_objectid(id)})

    if flight is None:
        raise HTTPException(404, "Flight not found")

    await flight_collection.delete_one({"_id": to_objectid(id)})
    return FlightDisplaySchema(**flight_display_helper(flight))
