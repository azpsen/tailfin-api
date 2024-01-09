import datetime
from typing import Optional, Dict, Union, List

from bson import ObjectId
from pydantic import BaseModel

from database.aircraft import retrieve_aircraft_by_id
from schemas.utils import PositiveFloatNullable, PositiveFloat, PositiveInt, PyObjectId


class FlightSchema(BaseModel):
    date: datetime.datetime
    waypoint_from: Optional[str] = None
    waypoint_to: Optional[str] = None
    route: Optional[str] = None

    hobbs_start: Optional[PositiveFloatNullable] = None
    hobbs_end: Optional[PositiveFloatNullable] = None
    tach_start: Optional[PositiveFloatNullable] = None
    tach_end: Optional[PositiveFloatNullable] = None

    time_start: Optional[datetime.datetime] = None
    time_off: Optional[datetime.datetime] = None
    time_down: Optional[datetime.datetime] = None
    time_stop: Optional[datetime.datetime] = None

    time_total: PositiveFloat
    time_pic: PositiveFloat
    time_sic: PositiveFloat
    time_night: PositiveFloat
    time_solo: PositiveFloat

    time_xc: PositiveFloat
    dist_xc: PositiveFloat

    landings_day: PositiveInt
    landings_night: PositiveInt

    time_instrument: PositiveFloat
    time_sim_instrument: PositiveFloat
    holds_instrument: PositiveInt

    dual_given: PositiveFloat
    dual_recvd: PositiveFloat
    time_sim: PositiveFloat
    time_ground: PositiveFloat

    tags: list[str] = []

    pax: list[str] = []
    crew: list[str] = []

    comments: Optional[str] = None


class FlightCreateSchema(FlightSchema):
    aircraft: str


class FlightDisplaySchema(FlightSchema):
    user: PyObjectId
    id: PyObjectId
    aircraft: PyObjectId


class FlightConciseSchema(BaseModel):
    user: PyObjectId
    id: PyObjectId
    aircraft: str

    date: datetime.date
    aircraft: str
    waypoint_from: Optional[str] = None
    waypoint_to: Optional[str] = None

    time_total: PositiveFloat

    comments: Optional[str] = None


FlightByDateSchema = Dict[int, Union[List['FlightByDateSchema'], FlightConciseSchema]]


# HELPERS #


def flight_display_helper(flight: dict) -> dict:
    """
    Convert given db response to a format usable by FlightDisplaySchema

    :param flight: Database response
    :return: Usable dict
    """
    flight["id"] = str(flight["_id"])
    flight["user"] = str(flight["user"])
    flight["aircraft"] = str(flight["aircraft"])

    return flight


async def flight_concise_helper(flight: dict) -> dict:
    """
    Convert given db response to a format usable by FlightConciseSchema

    :param flight: Database response
    :return: Usable dict
    """
    flight["id"] = str(flight["_id"])
    flight["user"] = str(flight["user"])
    flight["aircraft"] = (await retrieve_aircraft_by_id(str(flight["aircraft"]))).tail_no

    return flight


def flight_add_helper(flight: dict, user: str) -> dict:
    """
    Convert given flight schema and user string to a format that can be inserted into the db

    :param flight: Flight request body
    :param user: User that created flight
    :return: Combined dict that can be inserted into db
    """
    flight["user"] = ObjectId(user)
    flight["aircraft"] = ObjectId(flight["aircraft"])

    return flight
