import logging
import mimetypes
import os

from fastapi import APIRouter, UploadFile, File, Path, Depends, HTTPException
from starlette.responses import StreamingResponse

from app.deps import get_current_user
from database import img
from schemas.user import UserDisplaySchema, AuthLevel

router = APIRouter()

logger = logging.getLogger("img")


@router.get("/{image_id}", description="Retrieve an image from the database")
async def get_image(user: UserDisplaySchema = Depends(get_current_user),
                    image_id: str = Path(..., description="ID of image to retrieve")) -> StreamingResponse:
    """
    Retrieve an image from the database

    :param user: Current user
    :param image_id: ID of image to retrieve
    :return: Stream associated with requested image
    """
    stream, user_created = await img.retrieve_image(image_id)

    if not user.id == user_created and not user.level == AuthLevel.ADMIN:
        raise HTTPException(403, "Access denied")

    file_extension = os.path.splitext(image_id)[1]
    media_type = mimetypes.types_map.get(file_extension)

    return StreamingResponse(stream, media_type=media_type)


@router.post("/upload", description="Upload an image to the database")
async def upload_image(user: UserDisplaySchema = Depends(get_current_user),
                       image: UploadFile = File(..., description="Image file to upload")) -> dict:
    """
    Upload the given image to the database

    :param user: Current user
    :param image: Image to upload
    :return: Image filename and id
    """
    return await img.upload_image(image, str(user.id))


@router.delete("/{image_id}", description="Delete the given image from the database")
async def delete_image(user: UserDisplaySchema = Depends(get_current_user),
                       image_id: str = Path(..., description="ID of image to delete")):
    """
    Delete the given image from the database

    :param user: Current user
    :param image_id: ID of image to delete
    :return:
    """
    metadata = await img.retrieve_image_metadata(image_id)

    if not user.id == metadata["user"] and not user.level == AuthLevel.ADMIN:
        raise HTTPException(403, "Access denied")

    if metadata is None:
        raise HTTPException(404, "Image not found")

    return await img.delete_image(image_id)
