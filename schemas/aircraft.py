from enum import Enum
from typing import Annotated

from pydantic import BaseModel, field_validator, Field
from pydantic_core.core_schema import ValidationInfo

from schemas.flight import PyObjectId


class AircraftCategory(Enum):
    airplane = "Airplane"
    rotorcraft = "Rotorcraft"
    powered_lift = "Powered Lift"
    glider = "Glider"
    lighter_than_air = "Lighter-Than-Air"
    ppg = "Powered Parachute"
    weight_shift = "Weight-Shift Control"


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


PositiveFloat = Annotated[float, Field(default=0., ge=0)]


class AircraftCreateSchema(BaseModel):
    tail_no: str
    make: str
    model: str
    aircraft_category: AircraftCategory
    aircraft_class: AircraftClass

    hobbs: PositiveFloat
    tach: PositiveFloat

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
