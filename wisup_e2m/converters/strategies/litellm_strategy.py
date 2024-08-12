from wisup_e2m.converters.strategies.base import BaseStrategy
from litellm import LiteLLM
from typing import List
import base64
from mimetypes import guess_type


# Function to encode a local image into data URL
def local_image_to_data_url(image_path):
    # Guess the MIME type of the image based on the file extension
    mime_type, _ = guess_type(image_path)
    if mime_type is None:
        mime_type = "application/octet-stream"  # Default MIME type if none is found

    # Read and encode the image file
    with open(image_path, "rb") as image_file:
        base64_encoded_data = base64.b64encode(image_file.read()).decode("utf-8")

    # Construct the data URL
    return f"data:{mime_type};base64,{base64_encoded_data}"


class LitellmStrategy(BaseStrategy):

    def __init__(self, litellm_client: LiteLLM):
        self.litellm = litellm_client

    async def _query_async(self, messages, **kwargs):
        response = await self.litellm.chat.completions.create(
            messages=messages,
            model=kwargs.get("model"),
            temperature=kwargs.get("temperature"),
            top_p=kwargs.get("top_p"),
            n=kwargs.get("n"),
            max_tokens=kwargs.get("max_tokens"),
            presence_penalty=kwargs.get("presence_penalty"),
            frequency_penalty=kwargs.get("frequency_penalty"),
            acompletion=True,
        )

        return response.choices[0].message.content

    def _query(self, messages, verbose=True, **kwargs):
        response = self.litellm.chat.completions.create(
            messages=messages,
            model=kwargs.get("model"),
            temperature=kwargs.get("temperature"),
            top_p=kwargs.get("top_p"),
            n=kwargs.get("n"),
            max_tokens=kwargs.get("max_tokens"),
            presence_penalty=kwargs.get("presence_penalty"),
            frequency_penalty=kwargs.get("frequency_penalty"),
            stream=True,
        )

        full_text = []

        for chunk in response:
            content = chunk.choices[0].delta.content
            if verbose:
                print(content, end="")
            if content:
                full_text.append(content)

        return "".join(full_text)

    def default_text_convert(self, text: str, verbose: bool = True, **kwargs) -> str:
        messages = [
            {
                "role": "user",
                "content": f"请把下面内容转换为markdown格式:{text}",
            }
        ]

        return self._query(messages, verbose=verbose, **kwargs)

    def default_image_convert(
        self, images: List[str], verbose: bool = True, **kwargs
    ) -> str:
        messages = [
            {
                "role": "user",
                "content": [{"type": "text", "text": "请把图片转换为markdown格式"}],
            }
        ]

        # When uploading images, there is a limit of 10 images per chat request.
        for image in images:
            messages[0]["content"].append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": (
                            local_image_to_data_url(image)
                            if not image.startswith("http")
                            else image
                        ),
                    },
                }
            )

        return self._query(messages, verbose=verbose, **kwargs)

    def with_toc_text_convert(self, text: str, verbose: bool = True, **kwargs) -> str:
        # 先识别出目录

        # 根据目录来修复文本
        pass

    def with_toc_image_convert(
        self, images: List[str], verbose: bool = True, **kwargs
    ) -> str:
        # 先识别出目录

        # 根据目录来修复文本
        pass
