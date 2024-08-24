import logging
from functools import wraps
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


def api_error_handler(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            raise e

        except httpx.RequestError as e:
            logger.error(f"Request error occurred: {e}")
            raise e

    return wrapper


def api_error_handler_async(func):

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            raise e

        except httpx.RequestError as e:
            logger.error(f"Request error occurred: {e}")
            raise e

    return wrapper


@api_error_handler
def get_web_content(url: str, client: Optional[httpx.Client] = None) -> str:
    if client is None:
        client = httpx.Client()

    response = client.get(url)
    return response.text


@api_error_handler_async
async def get_web_content_async(url: str, client: Optional[httpx.AsyncClient] = None) -> str:
    if client is None:
        client = httpx.AsyncClient()

    response = await client.get(url)
    return response.text


@api_error_handler
def download_internet_image(
    image_url: str,
    target_path: str,
    client: Optional[httpx.Client] = None,
    force_format: Optional[str] = None,
):
    if client is None:
        client = httpx.Client()

    response = client.get(image_url)

    # todo: handle force_format
    if force_format:
        logger.warning(f"Currently not handling force_format: {force_format}")

    with open(target_path, "wb") as f:
        f.write(response.content)


@api_error_handler_async
async def download_internet_image_async(
    image_url: str, target_path: str, client: Optional[httpx.AsyncClient] = None
):
    if client is None:
        client = httpx.AsyncClient()

    response = await client.get(image_url)
    with open(target_path, "wb") as f:
        f.write(response.content)


if __name__ == "__main__":
    download_internet_image(
        image_url="https://www.techspot.com/images2/news/bigimage/2024/05/2024-05-05-image-j.webp",
        target_path="test.webp",
    )
