import datetime
import typing
from typing import Optional, Dict, Union, List

from bson import ObjectId
from fastapi import UploadFile, File
from pydantic import BaseModel

from schemas.utils import PositiveFloatNullable, PositiveFloat, PositiveInt, PyObjectId


class FlightSchema(BaseModel):
    date: datetime.datetime
    aircraft: str
    waypoint_from: Optional[str] = None
    waypoint_to: Optional[str] = None
    route: Optional[str] = None

    hobbs_start: Optional[PositiveFloatNullable] = None
    hobbs_end: Optional[PositiveFloatNullable] = None

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

    tags: List[str] = []

    pax: List[str] = []
    crew: List[str] = []

    comments: Optional[str] = None


class FlightCreateSchema(FlightSchema):
    images: List[str] = []


class FlightPatchSchema(BaseModel):
    date: Optional[datetime.datetime] = None
    aircraft: Optional[str] = None
    waypoint_from: Optional[str] = None
    waypoint_to: Optional[str] = None
    route: Optional[str] = None

    hobbs_start: Optional[PositiveFloatNullable] = None
    hobbs_end: Optional[PositiveFloatNullable] = None

    time_start: Optional[datetime.datetime] = None
    time_off: Optional[datetime.datetime] = None
    time_down: Optional[datetime.datetime] = None
    time_stop: Optional[datetime.datetime] = None

    time_total: Optional[PositiveFloat] = None
    time_pic: Optional[PositiveFloat] = None
    time_sic: Optional[PositiveFloat] = None
    time_night: Optional[PositiveFloat] = None
    time_solo: Optional[PositiveFloat] = None

    time_xc: Optional[PositiveFloat] = None
    dist_xc: Optional[PositiveFloat] = None

    landings_day: Optional[PositiveInt] = None
    landings_night: Optional[PositiveInt] = None

    time_instrument: Optional[PositiveFloat] = None
    time_sim_instrument: Optional[PositiveFloat] = None
    holds_instrument: Optional[PositiveInt] = None

    dual_given: Optional[PositiveFloat] = None
    dual_recvd: Optional[PositiveFloat] = None
    time_sim: Optional[PositiveFloat] = None
    time_ground: Optional[PositiveFloat] = None

    tags: Optional[List[str]] = None

    pax: Optional[List[str]] = None
    crew: Optional[List[str]] = None

    images: Optional[List[str]] = None

    comments: Optional[str] = None


class FlightDisplaySchema(FlightCreateSchema):
    user: PyObjectId
    id: PyObjectId


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


FlightByDateSchema = Dict[int, Union[Dict[int, 'FlightByDateSchema'], FlightConciseSchema]]


# HELPERS #

def flight_display_helper(flight: dict) -> dict:
    """
    Convert given db response to a format usable by FlightDisplaySchema

    :param flight: Database response
    :return: Usable dict
    """
    flight["id"] = str(flight["_id"])
    flight["user"] = str(flight["user"])

    return flight


async def flight_concise_helper(flight: dict) -> dict:
    """
    Convert given db response to a format usable by FlightConciseSchema

    :param flight: Database response
    :return: Usable dict
    """
    flight["id"] = str(flight["_id"])
    flight["user"] = str(flight["user"])

    return flight


def flight_add_helper(flight: dict, user: str) -> dict:
    """
    Convert given flight schema and user string to a format that can be inserted into the db

    :param flight: Flight request body
    :param user: User that created flight
    :return: Combined dict that can be inserted into db
    """
    flight["user"] = ObjectId(user)

    return flight
