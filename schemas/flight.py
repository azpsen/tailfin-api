import datetime
from typing import Optional, Annotated, Any

from bson import ObjectId
from pydantic import BaseModel, Field
from pydantic_core import core_schema

PositiveInt = Annotated[int, Field(default=0, ge=0)]
PositiveFloat = Annotated[float, Field(default=0., ge=0)]
PositiveFloatNullable = Annotated[float, Field(ge=0)]


class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(
            cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, value) -> ObjectId:
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")

        return ObjectId(value)


class FlightCreateSchema(BaseModel):
    date: datetime.datetime
    aircraft: Optional[str] = None
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

    takeoffs_day: PositiveInt
    landings_day: PositiveInt
    takeoffs_night: PositiveInt
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


class FlightDisplaySchema(FlightCreateSchema):
    user: PyObjectId
    id: PyObjectId


class FlightConciseSchema(BaseModel):
    user: PyObjectId
    id: PyObjectId

    date: datetime.date
    aircraft: str
    waypoint_from: Optional[str] = None
    waypoint_to: Optional[str] = None

    time_total: PositiveFloat

    comments: Optional[str] = None
