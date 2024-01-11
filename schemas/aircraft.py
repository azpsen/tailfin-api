from enum import Enum

from bson import ObjectId
from pydantic import BaseModel, field_validator
from pydantic_core.core_schema import ValidationInfo

from schemas.utils import PyObjectId, PositiveFloat

category_class = {
    "Airplane": [
        "Single-Engine Land",
        "Multi-Engine Land",
        "Single-Engine Sea",
        "Multi-Engine Sea",
    ],
    "Rotorcraft": [
        "Helicopter",
        "Gyroplane",
    ],
    "Powered Lift": [
        "Powered Lift",
    ],
    "Glider": [
        "Glider",
    ],
    "Lighter-Than-Air": [
        "Airship",
        "Balloon",
    ],
    "Powered Parachute": [
        "Powered Parachute Land",
        "Powered Parachute Sea",
    ],
    "Weight-Shift Control": [
        "Weight-Shift Control Land",
        "Weight-Shift Control Sea",
    ],
}


class AircraftCategory(Enum):
    airplane = "Airplane"
    rotorcraft = "Rotorcraft"
    powered_lift = "Powered Lift"
    glider = "Glider"
    lighter_than_air = "Lighter-Than-Air"
    ppg = "Powered Parachute"
    weight_shift = "Weight-Shift Control"


aircraft_category_dict = {cls.name: cls.value for cls in AircraftCategory}


class AircraftClass(Enum):
    # Airplane
    sel = "Single-Engine Land"
    ses = "Single-Engine Sea"
    mel = "Multi-Engine Land"
    mes = "Multi-Engine Sea"

    # Rotorcraft
    helicopter = "Helicopter"
    gyroplane = "Gyroplane"

    # Powered Lift
    powered_lift = "Powered Lift"

    # Glider
    glider = "Glider"

    # Lighther-than-air
    airship = "Airship"
    balloon = "Balloon"

    # Powered Parachute
    ppl = "Powered Parachute Land"
    pps = "Powered Parachute Sea"

    # Weight-Shift
    wsl = "Weight-Shift Control Land"
    wss = "Weight-Shift Control Sea"


aircraft_class_dict = {cls.name: cls.value for cls in AircraftClass}


class AircraftCreateSchema(BaseModel):
    tail_no: str
    make: str
    model: str
    aircraft_category: AircraftCategory
    aircraft_class: AircraftClass

    hobbs: PositiveFloat

    @field_validator('aircraft_class')
    def validate_class(cls, v: str, info: ValidationInfo, **kwargs):
        """
        Dependent field validator for aircraft class. Ensures class corresponds to the correct category

        :param v: Value of aircraft_class
        :param values: Other values in schema
        :param kwargs:
        :return: v
        """
        if 'aircraft_category' in info.data.keys():
            category = info.data['aircraft_category']
            if category == AircraftCategory.airplane and v not in [AircraftClass.sel, AircraftClass.mel,
                                                                   AircraftClass.ses, AircraftClass.mes]:
                raise ValueError("Class must be SEL, MEL, SES, or MES for Airplane category")
            elif category == AircraftCategory.rotorcraft and v not in [AircraftClass.helicopter,
                                                                       AircraftClass.gyroplane]:
                raise ValueError("Class must be Helicopter or Gyroplane for Rotorcraft category")
            elif category == AircraftCategory.powered_lift and not v == AircraftClass.powered_lift:
                raise ValueError("Class must be Powered Lift for Powered Lift category")
            elif category == AircraftCategory.glider and not v == AircraftClass.glider:
                raise ValueError("Class must be Glider for Glider category")
            elif category == AircraftCategory.lighter_than_air and v not in [
                AircraftClass.airship, AircraftClass.balloon]:
                raise ValueError("Class must be Airship or Balloon for Lighter-Than-Air category")
            elif category == AircraftCategory.ppg and v not in [AircraftClass.ppl,
                                                                AircraftClass.pps]:
                raise ValueError("Class must be Powered Parachute Land or "
                                 "Powered Parachute Sea for Powered Parachute category")
            elif category == AircraftCategory.weight_shift and v not in [AircraftClass.wsl,
                                                                         AircraftClass.wss]:
                raise ValueError("Class must be Weight-Shift Control Land or Weight-Shift "
                                 "Control Sea for Weight-Shift Control category")
        return v


class AircraftDisplaySchema(AircraftCreateSchema):
    user: PyObjectId
    id: PyObjectId


# HELPERS #


def aircraft_add_helper(aircraft: dict, user: str) -> dict:
    """
    Convert given aircraft dict to a format that can be inserted into the db

    :param aircraft: Aircraft request body
    :param user: User that created aircraft
    :return: Combined dict that can be inserted into db
    """
    aircraft["user"] = ObjectId(user)
    aircraft["aircraft_category"] = aircraft["aircraft_category"].name
    aircraft["aircraft_class"] = aircraft["aircraft_class"].name

    return aircraft


def aircraft_display_helper(aircraft: dict) -> dict:
    """
    Convert given db response into a format usable by AircraftDisplaySchema

    :param aircraft:
    :return: USable dict
    """
    aircraft["id"] = str(aircraft["_id"])
    aircraft["user"] = str(aircraft["user"])

    if aircraft["aircraft_category"] is not AircraftCategory:
        aircraft["aircraft_category"] = AircraftCategory.__members__.get(aircraft["aircraft_category"])

    if aircraft["aircraft_class"] is not AircraftClass:
        aircraft["aircraft_class"] = AircraftClass.__members__.get(aircraft["aircraft_class"])

    return aircraft
