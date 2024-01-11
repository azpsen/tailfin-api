from typing import Any

from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import WriteError

from database.db import aircraft_collection
from schemas.aircraft import AircraftDisplaySchema, AircraftCreateSchema, aircraft_display_helper, aircraft_add_helper


async def retrieve_aircraft(user: str = "") -> list[AircraftDisplaySchema]:
    """
    Retrieve a list of aircraft, optionally filtered by user

    :param user: User to filter aircraft by
    :return: List of aircraft
    """
    aircraft = []
    if user == "":
        async for doc in aircraft_collection.find():
            aircraft.append(AircraftDisplaySchema(**aircraft_display_helper(doc)))
    else:
        async for doc in aircraft_collection.find({"user": ObjectId(user)}):
            aircraft.append(AircraftDisplaySchema(**aircraft_display_helper(doc)))

    return aircraft


async def retrieve_aircraft_by_tail(tail_no: str) -> AircraftDisplaySchema:
    """
    Retrieve details about the requested aircraft

    :param tail_no: Tail number of desired aircraft
    :return: Aircraft details
    """
    aircraft = await aircraft_collection.find_one({"tail_no": tail_no})

    if aircraft is None:
        raise HTTPException(404, "Aircraft not found")

    return AircraftDisplaySchema(**aircraft_display_helper(aircraft))


async def retrieve_aircraft_by_id(id: str) -> AircraftDisplaySchema:
    """
    Retrieve details about the requested aircraft

    :param tail_no: Tail number of desired aircraft
    :return: Aircraft details
    """
    aircraft = await aircraft_collection.find_one({"_id": ObjectId(id)})

    if aircraft is None:
        raise HTTPException(404, "Aircraft not found")

    return AircraftDisplaySchema(**aircraft_display_helper(aircraft))


async def insert_aircraft(body: AircraftCreateSchema, id: str) -> ObjectId:
    """
    Insert a new aircraft into the database

    :param body: Aircraft data
    :param id: ID of creating user
    :return: ID of inserted aircraft
    """
    aircraft = await aircraft_collection.insert_one(aircraft_add_helper(body.model_dump(), id))
    return aircraft.inserted_id


async def update_aircraft(body: AircraftCreateSchema, id: str) -> AircraftDisplaySchema:
    """
    Update given aircraft in the database

    :param body: Updated aircraft data
    :param id: ID of aircraft to update
    :return: Updated aircraft
    """
    aircraft = await aircraft_collection.find_one({"_id": ObjectId(id)})

    if aircraft is None:
        raise HTTPException(404, "Aircraft not found")

    updated_aircraft = await aircraft_collection.update_one({"_id": ObjectId(id)}, {"$set": body.model_dump()})
    if updated_aircraft is None:
        raise HTTPException(500, "Failed to update flight")

    return AircraftDisplaySchema(**body.model_dump())


async def update_aircraft_field(field: str, value: Any, id: str) -> AircraftDisplaySchema:
    """
    Update a single field of the given aircraft in the database

    :param field: Field to update
    :param value: Value to set field to
    :param id: ID of aircraft to update
    :return: Updated aircraft
    """
    aircraft = await aircraft_collection.find_one({"_id": ObjectId(id)})

    if aircraft is None:
        raise HTTPException(404, "Aircraft not found")

    try:
        updated_aircraft = await aircraft_collection.update_one({"_id": ObjectId(id)}, {"$set": {field: value}})
    except WriteError as e:
        raise HTTPException(400, e.details)

    if updated_aircraft is None:
        raise HTTPException(500, "Failed to update flight")

    return AircraftDisplaySchema(**aircraft.model_dump())


async def delete_aircraft(id: str) -> AircraftDisplaySchema:
    """
    Delete the given aircraft from the database

    :param id: ID of aircraft to delete
    :return: Deleted aircraft information
    """
    aircraft = await aircraft_collection.find_one({"_id": ObjectId(id)})

    if aircraft is None:
        raise HTTPException(404, "Aircraft not found")

    await aircraft_collection.delete_one({"_id": ObjectId(id)})
    return AircraftDisplaySchema(**aircraft_display_helper(aircraft))
