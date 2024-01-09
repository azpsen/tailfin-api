from typing import Any, Annotated

from bson import ObjectId
from pydantic import Field, AfterValidator
from pydantic_core import core_schema


def round_two_decimal_places(value: Any) -> Any:
    """
    Round the given value to two decimal places if it is a float, otherwise return the original value

    :param value: Value to round
    :return: Rounded value
    """
    if isinstance(value, float):
        return round(value, 2)
    return value


PositiveInt = Annotated[int, Field(default=0, ge=0)]
PositiveFloat = Annotated[float, Field(default=0., ge=0), AfterValidator(round_two_decimal_places)]
PositiveFloatNullable = Annotated[float, Field(ge=0), AfterValidator(round_two_decimal_places)]


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
