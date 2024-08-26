import logging
from pathlib import Path
from typing import Dict, List, Optional

from litellm import LiteLLM, acompletion, completion, get_model_info

from wisup_e2m.converters.strategies.base import BaseStrategy
from wisup_e2m.converters.strategies.prompts import (
    CONTINUE_NOTION,
    DEFAULT_IMAGE_ROLE,
    DEFAULT_TEXT_ROLE,
    FORMAT_INFERENCE_INSTRUCTION,
    NEWLINE_NOTION,
    TEXT_FORMAT_INFERENCE_ROLE,
)
from wisup_e2m.utils.image_util import local_image_to_data_url
from wisup_e2m.utils.llm_utils import LlmUtils

logger = logging.getLogger(__name__)

_completion_params = [
    "model",
    "temperature",
    "top_p",
    "n",
    "max_tokens",
    "presence_penalty",
    "frequency_penalty",
    "api_key",
    "base_url",
    "caching",
]


class LitellmStrategy(BaseStrategy):
    TYPE = "litellm"

    def __init__(self, litellm_client: Optional[LiteLLM] = None):
        self.litellm_client = litellm_client

    async def _query_async(self, messages, **completion_kwargs):
        if not self.litellm_client:
            response = await acompletion(
                messages=messages,
                model=completion_kwargs.get("model"),
                temperature=completion_kwargs.get("temperature"),
                top_p=completion_kwargs.get("top_p"),
                n=completion_kwargs.get("n"),
                max_tokens=completion_kwargs.get("max_tokens"),
                presence_penalty=completion_kwargs.get("presence_penalty"),
                frequency_penalty=completion_kwargs.get("frequency_penalty"),
                api_key=completion_kwargs.get("api_key"),
                base_url=completion_kwargs.get("base_url"),
                caching=completion_kwargs.get("caching"),
            )
        else:
            response = await self.litellm_client.chat.completions.create(
                messages=messages,
                model=completion_kwargs.get("model"),
                temperature=completion_kwargs.get("temperature"),
                top_p=completion_kwargs.get("top_p"),
                n=completion_kwargs.get("n"),
                max_tokens=completion_kwargs.get("max_tokens"),
                presence_penalty=completion_kwargs.get("presence_penalty"),
                frequency_penalty=completion_kwargs.get("frequency_penalty"),
                acompletion=True,
            )

        messages.append(
            {
                "role": "assistant",
                "content": response.choices[0].message.content,
            }
        )

        return response.choices[0].message.content

    def _query(self, messages, verbose=True, **completion_kwargs):
        if not self.litellm_client:
            logging.info("Using the default LiteLLM client.")
            response = completion(
                messages=messages,
                model=completion_kwargs.get("model"),
                temperature=completion_kwargs.get("temperature"),
                top_p=completion_kwargs.get("top_p"),
                n=completion_kwargs.get("n"),
                max_tokens=completion_kwargs.get("max_tokens"),
                presence_penalty=completion_kwargs.get("presence_penalty"),
                frequency_penalty=completion_kwargs.get("frequency_penalty"),
                caching=completion_kwargs.get("caching"),
                api_key=completion_kwargs.get("api_key"),
                base_url=completion_kwargs.get("base_url"),
                stream=True,
            )
        else:
            response = self.litellm_client.chat.completions.create(
                messages=messages,
                model=completion_kwargs.get("model"),
                temperature=completion_kwargs.get("temperature"),
                top_p=completion_kwargs.get("top_p"),
                n=completion_kwargs.get("n"),
                max_tokens=completion_kwargs.get("max_tokens"),
                presence_penalty=completion_kwargs.get("presence_penalty"),
                frequency_penalty=completion_kwargs.get("frequency_penalty"),
                cache=completion_kwargs.get("cache"),
                stream=True,
            )

        full_text = []

        for chunk in response:
            content = chunk.choices[0].delta.content
            if verbose:
                print(content, end="")
            if content:
                full_text.append(content)

        content = "".join(full_text)

        messages.append(
            {
                "role": "assistant",
                "content": content,
            }
        )

        return content

    def text_format_inference(
        self,
        text: Optional[str] = None,
        images: Optional[str] = None,
        verbose: bool = True,
        **kwargs,
    ) -> str:
        if text is None and images is None:
            raise ValueError("Either text or image must be provided.")

        if text and images:
            raise ValueError("Only one of text or image can be provided.")

        if text:
            messages = [
                {
                    "role": "system",
                    "content": TEXT_FORMAT_INFERENCE_ROLE,
                },
                {
                    "role": "user",
                    "content": text,
                },
            ]
        if images:
            messages = [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": TEXT_FORMAT_INFERENCE_ROLE}],
                },
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

    def default_text_convert(self, text: str, verbose: bool = True, **kwargs) -> str:
        model = kwargs.get("model", None)
        max_tokens = kwargs.get("max_tokens", None)

        inferenced_text_format = self.text_format_inference(
            text=text[: LlmUtils.estimate_token_to_char(get_model_info(model)["max_input_tokens"])],
            verbose=verbose,
            **kwargs,
        )

        chunks = _break_text_into_chunks(
            text=text,
            overlap=0,
            model=model,
            max_tokens=max_tokens,
        )

        converted_text = []

        for idx, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {idx + 1}/{len(chunks)}")
            messages = [
                {
                    "role": "system",
                    "content": DEFAULT_TEXT_ROLE,
                },
                {
                    "role": "user",
                    "content": FORMAT_INFERENCE_INSTRUCTION.format(
                        inferenced_text_format=inferenced_text_format
                    ),
                },
            ]
            if idx != 0 and len(converted_text) > 0:
                messages.append(
                    {
                        "role": "user",
                        "content": f"前面部分已经修复的内容：\n{converted_text[-1][-200:]}",
                    }
                )
            messages.append(
                {
                    "role": "user",
                    "content": f"现在请把下面的文本完整转换成Markdown格式,保证能连接上已修复的内容：\n{chunk}",
                }
            )

            logger.info(f"Sending messages to the model: \n{messages}")

            converted_text.append(
                LlmUtils.clean_to_markdown(self._query(messages, verbose=verbose, **kwargs))
            )

        # 去除所有的`<CONTINUE>`和`<END>`,  <CONTINUE> -> "", <END> -> "\n"
        return "".join(
            [
                text.replace(f"`{CONTINUE_NOTION}`", "")
                .replace(f"`{NEWLINE_NOTION}`", "")
                .replace(CONTINUE_NOTION, "")
                .replace(NEWLINE_NOTION, "\n")
                for text in converted_text
            ]
        )

    def default_image_convert(
        self,
        images: List[str],
        attached_images_map: Dict[str, List[str]],
        verbose: bool = True,
        image_batch_size: int = 5,
        **kwargs,
    ) -> str:

        # 取前10张图片进行格式推断
        inferenced_text_format = self.text_format_inference(
            images=images[:10], verbose=verbose, **kwargs
        )

        converted_text = []

        for idx in range(0, len(images), image_batch_size):
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": DEFAULT_IMAGE_ROLE},
                        {
                            "type": "text",
                            "text": FORMAT_INFERENCE_INSTRUCTION.format(
                                inferenced_text_format=inferenced_text_format
                            ),
                        },
                    ],
                },
            ]

            # When uploading images, there is a limit of 10 images per chat request.
            for image in images[idx : idx + image_batch_size]:
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

                # 获取 attached_images
                image_name = Path(image).name
                if attached_images_map:
                    tmp_attached_images = attached_images_map.get(image_name, [])

                    # 添加content说明，你可以使用的图片
                    if tmp_attached_images:
                        messages[0]["content"].append(
                            {
                                "type": "text",
                                "text": f"你可以使用以下图片：\n{tmp_attached_images}",
                            }
                        )

            if idx != 0 and len(converted_text) > 0:
                messages[0]["content"].append(
                    {
                        "type": "text",
                        "text": f"前面部分已经修复的内容的末尾：\n{converted_text[-1][-100:]}",
                    }
                )

            converted_text.append(
                LlmUtils.clean_to_markdown(self._query(messages, verbose=verbose, **kwargs))
            )

        return "".join(
            [
                text.replace(f"`{CONTINUE_NOTION}`", "")
                .replace(f"`{NEWLINE_NOTION}`", "\n")
                .replace(CONTINUE_NOTION, "")
                .replace(NEWLINE_NOTION, "\n")
                for text in converted_text
            ]
        )

    def with_toc_text_convert(self, text: str, verbose: bool = True, **kwargs) -> str:
        # 先识别出目录

        # 根据目录来修复文本

        raise NotImplementedError("Not implemented yet.")

    def with_toc_image_convert(self, images: List[str], verbose: bool = True, **kwargs) -> str:
        # 先识别出目录

        # 根据目录来修复文本

        raise NotImplementedError("Not implemented yet.")


def _break_text_into_chunks(
    text: str,
    model: str,
    overlap: int = 300,
    custom_llm_provider: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> List[str]:
    model_info = get_model_info(model, custom_llm_provider)
    logger.info(f"Model info: {model_info}")
    max_output_tokens = model_info["max_output_tokens"]
    if not max_tokens or max_tokens > max_output_tokens:
        logger.debug(
            f"max_tokens is not set or larger than the max_output_tokens of the model, using max_output_tokens instead: {max_output_tokens}"
        )
        max_tokens = max_output_tokens

    chunks = LlmUtils.break_text_into_chunks(text, (max_tokens) / 2, overlap)

    return chunks
