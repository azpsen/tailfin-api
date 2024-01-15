import io

from gridfs import NoFile

from .db import db_client as db, files_collection

import motor.motor_asyncio
from utils import to_objectid
from fastapi import UploadFile, File, HTTPException

fs = motor.motor_asyncio.AsyncIOMotorGridFSBucket(db)


async def upload_image(image: UploadFile = File(...), user: str = "") -> dict:
    """
    Take an image file and add it to the database, returning the filename and ID of the added image

    :param image: Image to upload
    :param user: ID of user uploading image to encode in image metadata
    :return: Dictionary with filename and file_id of newly added image
    """
    image_data = await image.read()

    metadata = {"user": user}

    file_id = await fs.upload_from_stream(image.filename, io.BytesIO(image_data), metadata=metadata)

    return {"filename": image.filename, "file_id": str(file_id)}


async def retrieve_image_metadata(image_id: str = "") -> dict:
    """
    Retrieve the metadata of a given image

    :param image_id: ID of image to retrieve metadata of
    :return: Image metadata
    """
    info = await files_collection.find_one({"_id": to_objectid(image_id)})

    if info is None:
        raise HTTPException(404, "Image not found")

    return info["metadata"]


async def retrieve_image(image_id: str = "") -> tuple[io.BytesIO, str]:
    """
    Retrieve the given image file from the database along with the user who created it

    :param image_id: ID of image to retrieve
    :return: BytesIO stream of image file, ID of user that uploaded the image
    """
    metadata = await retrieve_image_metadata(image_id)

    print(metadata)

    stream = io.BytesIO()
    try:
        await fs.download_to_stream(to_objectid(image_id), stream)
    except NoFile:
        raise HTTPException(404, "Image not found")

    stream.seek(0)

    return stream, metadata["user"] if metadata["user"] else ""


async def delete_image(image_id: str = ""):
    """
    Delete the given image from the database

    :param image_id: ID of image to delete
    :return: True if deleted
    """
    try:
        await fs.delete(to_objectid(image_id))
    except NoFile:
        raise HTTPException(404, "Image not found")
    except Exception as e:
        raise HTTPException(500, e)

    return True
