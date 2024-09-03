from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from wisup_e2m.parsers.base import E2MParsedData
from wisup_e2m.converters.base import ConvertHelpfulInfo


class ParseResponse(E2MParsedData):

    def set_image_to_base64(self):
        from wisup_e2m.utils.image_util import image_to_base64

        for image_data in self.images.values():
            if image_data.base64 is None:
                image_data.base64 = image_to_base64(image_data.image_path)

        for attached_image_data in self.attached_images.values():
            if attached_image_data.base64 is None:
                attached_image_data.base64 = image_to_base64(attached_image_data.image_path)


class ConvertResponse(BaseModel):
    converted_text: str


class ParseRequest(BaseModel):
    url: Optional[str] = None
    start_page: Optional[int] = None
    end_page: Optional[int] = None
    extract_images: bool = True
    include_image_link_in_text: bool = True
    relative_path: bool = True
    work_dir: Optional[str] = "./"
    image_dir: Optional[str] = "./figures"
    # ppt and pptx parser only
    include_page_breaks: bool = False
    include_slide_notes: bool = False
    ignore_transparent_images: bool = True

    @field_validator("url", mode="before")
    @classmethod
    def check_url(cls, v):
        return v


class ConvertRequest(BaseModel):
    text: Optional[str] = None
    images: Optional[List[str]] = None  # base64 encoded image list
    strategy: Optional[str] = "default"
    image_batch_size: Optional[int] = Field(5, le=10)  # max 10
    helpful_info: Optional[ConvertHelpfulInfo] = None

    @field_validator("image_batch_size")
    @classmethod
    def check_image_batch_size(cls, v):
        if v > 10:
            raise ValueError("image_batch_size must be 10 or less.")
        return v

    @field_validator("text", "images", mode="before")
    @classmethod
    def check_text_or_images(cls, v, info):
        if not v and not info.data.get("images"):
            raise ValueError("Either text or images must be provided.")
        return v

    @field_validator("images", mode="before")
    @classmethod
    def check_base64_encoded(cls, v):
        import base64

        try:
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError("Images must be base64 encoded.")
