from bson import ObjectId
from fastapi import HTTPException

from database.db import aircraft_collection
from database.utils import aircraft_display_helper, aircraft_add_helper
from schemas.aircraft import AircraftDisplaySchema, AircraftCreateSchema


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


async def retrieve_aircraft_by_id(id: str) -> AircraftDisplaySchema:
    """
    Retrieve details about the requested aircraft

    :param id: ID of desired aircraft
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
    :return: ID of updated aircraft
    """
    aircraft = await aircraft_collection.find_one({"_id": ObjectId(id)})

    if aircraft is None:
        raise HTTPException(404, "Aircraft not found")

    updated_aircraft = await aircraft_collection.update_one({"_id": ObjectId(id)}, {"$set": body.model_dump()})
    if updated_aircraft is None:
        raise HTTPException(500, "Failed to update flight")

    return id


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
