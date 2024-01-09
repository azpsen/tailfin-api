from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


def validate_username(value: str):
    length = len(value)
    if length < 4 or length > 32:
        raise ValueError("Username must be between 4 and 32 characters long")
    if any(not (x.isalnum() or x == "_" or x == " ") for x in value):
        raise ValueError("Username must only contain letters, numbers, underscores, and dashes")
    return value


def validate_password(value: str):
    length = len(value)
    if length < 8 or length > 16:
        raise ValueError("Password must be between 8 and 16 characters long")
    return value


class AuthLevel(Enum):
    GUEST = 0
    USER = 1
    ADMIN = 2

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return self.value == other.value
        return NotImplemented


class UserBaseSchema(BaseModel):
    username: str


class UserLoginSchema(UserBaseSchema):
    password: str


class UserCreateSchema(UserBaseSchema):
    password: str
    level: AuthLevel = Field(AuthLevel.USER)

    @field_validator("username")
    @classmethod
    def _valid_username(cls, value):
        return validate_username(value)

    @field_validator("password")
    @classmethod
    def _valid_password(cls, value):
        return validate_password(value)


class UserUpdateSchema(BaseModel):
    username: Optional[str] = None
    level: Optional[AuthLevel] = AuthLevel.USER

    @field_validator("username")
    @classmethod
    def _valid_username(cls, value):
        return validate_username(value)


class UserDisplaySchema(UserBaseSchema):
    id: str
    level: AuthLevel


class UserSystemSchema(UserDisplaySchema):
    password: str


class PasswordUpdateSchema(BaseModel):
    current_password: str = ...
    new_password: str = ...

    @field_validator("new_password")
    @classmethod
    def _valid_password(cls, value):
        return validate_password(value)


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str


class TokenPayload(BaseModel):
    sub: Optional[str]
    exp: Optional[int]


# HELPERS #


def user_helper(user) -> dict:
    """
    Convert given db response into a format usable by UserDisplaySchema

    :param user: Database response
    :return: Usable dict
    """
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "level": user["level"],
    }


def system_user_helper(user) -> dict:
    """
    Convert given db response to a format usable by UserSystemSchema

    :param user: Database response
    :return: Usable dict
    """
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "password": user["password"],
        "level": user["level"],
    }


def create_user_helper(user) -> dict:
    """
    Convert given db response to a format usable by UserCreateSchema

    :param user: Database response
    :return: Usable dict
    """
    return {
        "username": user["username"],
        "password": user["password"],
        "level": user["level"].value,
    }
