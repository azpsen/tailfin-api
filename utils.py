from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException


def to_objectid(id: str) -> ObjectId:
    """
    Try to convert a given string to an ObjectId

    :param id: ID in string form to convert
    :return: Converted ObjectId
    """
    try:
        oid = ObjectId(id)
        return oid
    except InvalidId:
        raise HTTPException(400, f"{id} is not a recognized ID")
