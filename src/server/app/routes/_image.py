from fastapi import APIRouter, status
from typing import List

from ..helpers._const import ImageResponse, SS
from ..helpers.image import get_image, get_image_hash, get_image_string


router = APIRouter()


@router.post("/ocr", status_code=status.HTTP_200_OK, response_model=List[ImageResponse])
async def read_items(_shots: List[SS]):

    _result: List[ImageResponse] = []

    for _ in _shots:
        _image = await get_image(_)
        if not _image:
            continue

        _result.append(
            ImageResponse(
                url=_.url,
                dhash=str(await get_image_hash(_image)),
                text=await get_image_string(_image),
            )
        )

    return _result
