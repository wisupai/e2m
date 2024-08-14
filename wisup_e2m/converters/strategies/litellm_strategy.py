from wisup_e2m.converters.strategies.base import BaseStrategy
from wisup_e2m.utils.image_util import local_image_to_data_url
from wisup_e2m.utils.llm_utils import LlmUtils
from litellm import LiteLLM, completion, acompletion
from litellm import get_model_info
from typing import List, Optional, Dict


import logging

logger = logging.getLogger(__name__)

CONTINUE_NOTION = "<CONTINUE>"
END_NOTION = "<END>"


class LitellmStrategy(BaseStrategy):
    TYPE = "litellm"

    def __init__(self, litellm_client: Optional[LiteLLM] = None):
        self.litellm_client = litellm_client

    async def _query_async(self, messages, **kwargs):
        if not self.litellm_client:
            response = await acompletion(
                messages=messages,
                model=kwargs.get("model"),
                temperature=kwargs.get("temperature"),
                top_p=kwargs.get("top_p"),
                n=kwargs.get("n"),
                max_tokens=kwargs.get("max_tokens"),
                presence_penalty=kwargs.get("presence_penalty"),
                frequency_penalty=kwargs.get("frequency_penalty"),
                api_key=kwargs.get("api_key"),
                base_url=kwargs.get("base_url"),
                caching=kwargs.get("caching"),
            )
        else:
            response = await self.litellm_client.chat.completions.create(
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
        if not self.litellm_client:
            response = completion(
                messages=messages,
                model=kwargs.get("model"),
                temperature=kwargs.get("temperature"),
                top_p=kwargs.get("top_p"),
                n=kwargs.get("n"),
                max_tokens=kwargs.get("max_tokens"),
                presence_penalty=kwargs.get("presence_penalty"),
                frequency_penalty=kwargs.get("frequency_penalty"),
                caching=kwargs.get("caching"),
                api_key=kwargs.get("api_key"),
                base_url=kwargs.get("base_url"),
                stream=True,
            )
        else:
            response = self.litellm_client.chat.completions.create(
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

        chunks = _break_text_into_chunks(
            text=text,
            overlap=0,
            model=kwargs.get("model", None),
            max_tokens=kwargs.get("max_tokens", None),
        )

        converted_text = []

        role_prompt = f"""你是一个能把文本准确的转换成Markdown格式的专家。

你需要遵循以下规则：
- 你生成的所有内容都将是markdown的正文，所以请你用```markdown<正文内容>```的形式表示。
- 如果我给你的文本末尾是被截断的，那么你最终生成的文本末尾也是被截断的，你将用在末尾用`{CONTINUE_NOTION}`表示，无需添加省略号等。
    - 对于未修复的文本，判断其是否被截断的标志是：
        1. 末尾标点符号是否完整；
        2. 末尾的语义是否完整；
- 如果我给你的文本末尾是完整的，那么你最终生成的文本末尾也是完整的，你将用在末尾用`{END_NOTION}`表示。
- 如果我需要你修复的文本内容开头部分和前面已修复的部分的末尾有重复，那么你无需输出重复内容，直接输出新的内容即可。
- 请你区分各级标题，使用Markdown标题符号，例如`#`、`##`、`###`等，来增强文本的结构关系。
- 所有的图片链接和数学公式都需要用markdown格式表示。
- 段落公式使用 $$ $$ 的形式、行内公式使用 $ $ 的形式、忽略掉长直线、忽略掉页码。
- 请不要使用html格式和语法。
- 请不要使用 `---` 作为分割符。
- 请不要省略文本中的任何内容，确保文本的连续性。
- 必要时，你可以重新排布文字的顺序，例如需要修复的文字是左右分块的。
- 请保证段落的连续性，不要在段落内随意换行。
- 你必须在结尾添加上`{CONTINUE_NOTION}` 或者 `{END_NOTION}` 符号。你会在结尾添加上符号。。
- 你必须确保所有的正文内容都被转换了，而不存在丢失的情况。
- 请你一步步思考，满足上面的要求。
---
如果我给你的文本并不是开头部分，那么我将同时给你文本的前面部分，你需要保证生成的文本是连续的。
"""

        for idx, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {idx + 1}/{len(chunks)}")
            messages = [
                {
                    "role": "system",
                    "content": role_prompt,
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
                LlmUtils.clean_to_markdown(
                    self._query(messages, verbose=verbose, **kwargs)
                )
            )

        # 去除所有的`<CONTINUE>`和`<END>`,  <CONTINUE> -> "", <END> -> "\n"
        return "".join(
            [
                text.replace(f"`{CONTINUE_NOTION}`", "")
                .replace(f"`{END_NOTION}`", "")
                .replace(CONTINUE_NOTION, "")
                .replace(END_NOTION, "\n")
                for text in converted_text
            ]
        )

    def default_image_convert(
        self,
        images: List[str],
        attached_images: Dict[str, List[str]],
        image_batch_size: int = 5,
        verbose: bool = True,
        **kwargs,
    ) -> str:
        role_prompt = f"""你是一个PDF文档解析器，使用markdown和latex语法输出图片的内容。
使用markdown语法，将图片中识别到的文字转换为markdown格式输出。你必须做到：
- 输出和使用识别到的图片的相同的语言，例如，识别到英语的字段，输出的内容必须是英语。
- 不要解释和输出无关的文字，直接输出图片中的内容。例如，严禁输出 “以下是我根据图片内容生成的markdown文本：”这样的例子，而是应该直接输出markdown。
- 内容不要包含在```markdown ```中、段落公式使用 $$ $$ 的形式、行内公式使用 $ $ 的形式、忽略掉长直线、忽略掉页码。
- 图片中用蓝色框和图片名称标注出了一些区域。如果区域是表格或者图片，使用 ![]() 的形式插入到输出内容中，否则直接输出文，图片地址、图片名称、图片注释可以从图片中提取。
- 请你确保图片和其名称是完全对应的，不要出现图片名称和图片内容不对应的情况。
- 再次强调，不要解释和输出无关的文字，不要出现错别字，直接输出图片中的内容。
- 不要生成 `---` 作为分割符。
- 你必须在结尾添加上{CONTINUE_NOTION} 或者 {END_NOTION} 符号。{CONTINUE_NOTION} 表示文本被截断，{END_NOTION} 表示文本完整。
"""

        converted_text = []

        for idx in range(0, len(images), image_batch_size):
            messages = [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": role_prompt}],
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
                tmp_attached_images = []
                if image in attached_images:
                    tmp_attached_images = attached_images[image]

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
                LlmUtils.clean_to_markdown(
                    self._query(messages, verbose=verbose, **kwargs)
                )
            )

        return "".join(
            [
                text.replace(f"`{CONTINUE_NOTION}`", "")
                .replace(f"`{END_NOTION}`", "\n")
                .replace(CONTINUE_NOTION, "")
                .replace(END_NOTION, "\n")
                for text in converted_text
            ]
        )

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


def _break_text_into_chunks(
    text: str,
    model: str,
    overlap: int = 300,
    custom_llm_provider: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> List[str]:
    model_info = get_model_info(model, custom_llm_provider)
    max_output_tokens = model_info["max_output_tokens"]
    if not max_tokens or max_tokens > max_output_tokens:
        logger.debug(
            f"max_tokens is not set or larger than the max_output_tokens of the model, using max_output_tokens instead: {max_output_tokens}"
        )
        max_tokens = max_output_tokens

    chunks = LlmUtils.break_text_into_chunks(text, (max_tokens) / 2, overlap)

    return chunks
