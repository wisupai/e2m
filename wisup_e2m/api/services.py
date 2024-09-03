import os
import logging
from typing import Optional, Union
import aiofiles
import aiofiles.os
from fastapi import UploadFile, HTTPException
from wisup_e2m.parsers.base import BaseParser, E2MParsedData
from wisup_e2m.parsers.main import E2MParser
from wisup_e2m.api.models import ParseRequest, ParseResponse, ConvertRequest, ConvertResponse
from wisup_e2m.api.config import UPLOAD_DIR

logger = logging.getLogger(__name__)


async def save_upload_file(upload_file: UploadFile) -> str:
    """
    Save the uploaded file to the specified upload directory.

    :param upload_file: The file to be uploaded.
    :return: The path where the file is saved.
    :raises HTTPException: If there's an error during file saving.
    """
    file_path = os.path.join(UPLOAD_DIR, upload_file.filename)
    try:
        async with aiofiles.open(file_path, "wb") as out_file:
            content = await upload_file.read()
            await out_file.write(content)
        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")


async def parse_file_service(
    file: Optional[UploadFile], request: ParseRequest, parser: Union[BaseParser, E2MParser]
) -> ParseResponse:
    """
    Parse the uploaded file or URL and return the parsed data.

    :param file: The uploaded file (optional).
    :param request: The parse request containing parameters.
    :param parser: The parser object to use for parsing.
    :return: ParseResponse containing the parsed data.
    :raises HTTPException: If there's an error during parsing or file handling.
    """
    file_path = None
    try:
        # Validate input: either file or URL must be provided
        if not file and not request.url:
            raise ValueError("Either file or URL must be provided")

        # Save the uploaded file if present
        if file:
            file_path = await save_upload_file(file)

        # Add a log before parsing
        logger.info(f"Starting to parse {'file' if file else 'URL'}")

        # Parse the file or URL
        parsed_data: E2MParsedData = parser.parse(
            file_name=file_path,
            url=request.url,
            start_page=request.start_page,
            end_page=request.end_page,
            extract_images=request.extract_images,
            include_image_link_in_text=request.include_image_link_in_text,
            work_dir=request.work_dir,
            image_dir=request.image_dir,
            relative_path=request.relative_path,
            include_page_breaks=request.include_page_breaks,
            include_slide_notes=request.include_slide_notes,
            ignore_transparent_images=request.ignore_transparent_images,
        )

        if not parsed_data:
            raise ValueError("No data found in the input file or URL")

        parse_response = ParseResponse(**parsed_data.to_dict())
        parse_response.set_image_to_base64()

        logger.info(f"Successfully parsed data for {'file' if file else 'URL'}")

        return parse_response

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in parse_file_service: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred during parsing")
    finally:
        # Clean up the temporary file
        if file_path:
            try:
                await aiofiles.os.remove(file_path)
            except Exception as e:
                logger.error(f"Failed to remove file: {str(e)}")


async def convert_data_service(request: ConvertRequest, converter) -> ConvertResponse:
    """
    Convert the input data to the target format.

    :param request: ConvertRequest object containing text, images, and related parameters to be converted
    :param converter: Converter object used to perform the conversion
    :return: ConvertResponse containing the converted data
    :raises HTTPException: When an error occurs during the conversion process
    """
    try:
        # Call the converter's convert method to perform data conversion
        converted_data = await converter.convert(
            text=request.text,
            images=request.images,
            strategy=request.strategy,
            image_batch_size=request.image_batch_size,
            helpful_info=request.helpful_info,
        )

        # Add a log after successful conversion
        logger.info("Data conversion completed successfully")

        return ConvertResponse(converted_text=converted_data)
    except ValueError as ve:
        # Raise a 400 error when input data is invalid
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Log other unexpected errors and raise a 500 error
        logger.error(f"Error in convert_data_service: {str(e)}")
        raise HTTPException(status_code=500, detail="Conversion error occurred")
