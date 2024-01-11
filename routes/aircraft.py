import logging

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user, admin_required
from database import aircraft as db
from schemas.aircraft import AircraftDisplaySchema, AircraftCreateSchema, category_class
from schemas.user import UserDisplaySchema, AuthLevel

router = APIRouter()

logger = logging.getLogger("aircraft")


@router.get('/', summary="Get aircraft created by the currently logged-in user", status_code=200)
async def get_aircraft(user: UserDisplaySchema = Depends(get_current_user)) -> list[AircraftDisplaySchema]:
    """
    Get a list of aircraft created by the currently logged-in user

    :param user: Current user
    :return: List of aircraft
    """
    aircraft = await db.retrieve_aircraft(user.id)
    return aircraft


@router.get('/all', summary="Get all aircraft created by all users", status_code=200,
            dependencies=[Depends(admin_required)], response_model=list[AircraftDisplaySchema])
async def get_all_aircraft() -> list[AircraftDisplaySchema]:
    """
    Get a list of all aircraft created by any user

    :return: List of aircraft
    """
    aircraft = await db.retrieve_aircraft()
    return aircraft


@router.get('/categories', summary="Get valid aircraft categories", status_code=200, response_model=dict)
async def get_categories() -> dict:
    """
    Get a list of valid aircraft categories

    :return: List of categories
    """
    return {"categories": list(category_class.keys())}


@router.get('/class', summary="Get valid aircraft classes for the given class", status_code=200, response_model=dict)
async def get_categories(category: str = "Airplane") -> dict:
    """
    Get a list of valid aircraft classes for the given class

    :return: List of classes
    """
    if category not in category_class.keys():
        raise HTTPException(404, "Category not found")

    return {"classes": category_class[category]}


@router.get('/id/{aircraft_id}', summary="Get details of a given aircraft", response_model=AircraftDisplaySchema,
            status_code=200)
async def get_aircraft_by_id(aircraft_id: str,
                             user: UserDisplaySchema = Depends(get_current_user)) -> AircraftDisplaySchema:
    """
    Get all details of a given aircraft

    :param aircraft_id: ID of requested aircraft
    :param user: Currently logged-in user
    :return: Aircraft details
    """
    aircraft = await db.retrieve_aircraft_by_id(aircraft_id)

    if str(aircraft.user) != user.id and AuthLevel(user.level) != AuthLevel.ADMIN:
        logger.info("Attempted access to unauthorized aircraft by %s", user.username)
        raise HTTPException(403, "Unauthorized access")

    return aircraft


@router.get('/tail/{tail_no}', summary="Get details of a given aircraft", response_model=AircraftDisplaySchema,
            status_code=200)
async def get_aircraft_by_tail(tail_no: str,
                               user: UserDisplaySchema = Depends(get_current_user)) -> AircraftDisplaySchema:
    """
    Get all details of a given aircraft

    :param tail_no: Tail number of requested aircraft
    :param user: Currently logged-in user
    :return: Aircraft details
    """
    aircraft = await db.retrieve_aircraft_by_tail(tail_no)

    if str(aircraft.user) != user.id and AuthLevel(user.level) != AuthLevel.ADMIN:
        logger.info("Attempted access to unauthorized aircraft by %s", user.username)
        raise HTTPException(403, "Unauthorized access")

    return aircraft


@router.post('/', summary="Add an aircraft", status_code=200)
async def add_aircraft(aircraft_body: AircraftCreateSchema,
                       user: UserDisplaySchema = Depends(get_current_user)) -> dict:
    """
    Add an aircraft to the database

    :param aircraft_body: Information associated with new aircraft
    :param user: Currently logged-in user
    :return: Error message if request invalid, else ID of newly created aircraft
    """

    try:
        await db.retrieve_aircraft_by_tail(aircraft_body.tail_no)
    except HTTPException:
        aircraft = await db.insert_aircraft(aircraft_body, user.id)

        return {"id": str(aircraft)}

    raise HTTPException(400, "Aircraft with tail number " + aircraft_body.tail_no + " already exists", )


@router.put('/{aircraft_id}', summary="Update the given aircraft with new information", status_code=200)
async def update_aircraft(aircraft_id: str, aircraft_body: AircraftCreateSchema,
                          user: UserDisplaySchema = Depends(get_current_user)) -> dict:
    """
    Update the given aircraft with new information

    :param aircraft_id: ID of aircraft to update
    :param aircraft_body: New aircraft information to update with
    :param user: Currently logged-in user
    :return: Updated aircraft
    """
    aircraft = await get_aircraft_by_id(aircraft_id, user)
    if aircraft is None:
        raise HTTPException(404, "Aircraft not found")

    if str(aircraft.user) != user.id and AuthLevel(user.level) != AuthLevel.ADMIN:
        logger.info("Attempted access to unauthorized aircraft by %s", user.username)
        raise HTTPException(403, "Unauthorized access")

    updated_aircraft_id = await db.update_aircraft(aircraft_body, aircraft_id, user.id)

    return {"id": str(updated_aircraft_id)}


@router.delete('/{aircraft_id}', summary="Delete the given aircraft", status_code=200,
               response_model=AircraftDisplaySchema)
async def delete_aircraft(aircraft_id: str,
                          user: UserDisplaySchema = Depends(get_current_user)) -> AircraftDisplaySchema:
    """
    Delete the given aircraft

    :param aircraft_id: ID of aircraft to delete
    :param user: Currently logged-in user
    :return: 200
    """
    aircraft = await get_aircraft_by_id(aircraft_id, user)

    if str(aircraft.user) != user.id and AuthLevel(user.level) != AuthLevel.ADMIN:
        logger.info("Attempted access to unauthorized aircraft by %s", user.username)
        raise HTTPException(403, "Unauthorized access")

    deleted = await db.delete_aircraft(aircraft_id)

    return deleted
