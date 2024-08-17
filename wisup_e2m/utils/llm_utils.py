import logging
import re

logger = logging.getLogger(__name__)


class LlmUtils:

    @staticmethod
    def break_text_into_chunks(text: str, max_tokens: int, overlap: int = 300) -> list[str]:
        """
        Break a given text into chunks based on a maximum number of tokens per chunk.

        This function uses the `estimate_char_to_token` function to estimate the number of tokens in each chunk.

        Args:
            text (str): The input text to be broken into chunks.
            max_tokens (int): The maximum number of tokens allowed per chunk.

        Returns:
            list[str]: A list of text chunks, where each chunk contains no more than `max_tokens` tokens.
        """
        chunks = []
        current_chunk = ""

        for line in text.split("\n"):
            if LlmUtils.estimate_char_to_token(current_chunk + line) <= max_tokens:
                current_chunk += line.strip() + "\n"
            else:
                chunks.append(current_chunk.strip())
                current_chunk = line.strip() + "\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        # Handle overlap, 在每一个chunk后面添加overlap个字符
        if overlap > 0:
            for i in range(1, len(chunks)):
                chunks[i] = chunks[i - 1][-overlap:] + chunks[i]

        return chunks

    @staticmethod
    def estimate_char_to_token(chars: str) -> int:
        """
        Estimate the number of tokens in a given string.

        This function follows the rule that 2 Chinese characters or 2 English words count as one token.

        Args:
            chars (str): The input string to estimate the number of tokens.

        Returns:
            int: The estimated number of tokens in the input string.
        """
        # Count the number of Chinese characters
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", chars))

        # Count the number of English words
        english_words = len(re.findall(r"\b\w+\b", chars))

        # Calculate the number of tokens
        num_tokens = chinese_chars // 2 + english_words // 2

        # Handle remaining characters
        remaining_chars = chinese_chars % 2 + english_words % 2
        num_tokens += (remaining_chars + 1) // 2

        return num_tokens

    @staticmethod
    def estimate_token_to_char(tokens: int) -> int:
        return tokens * 2

    @staticmethod
    def clean_to_markdown(content: str):
        # todo: add more rules or use a parser
        content = content.strip()
        if content.startswith("```markdown") and content.endswith("```"):
            content = content[11:-3]
        elif content.startswith("```") and content.endswith("```"):
            content = content[3:-3]
        elif content.startswith("```markdown") and not content.endswith("```"):
            logger.warning("Markdown code block not closed")
            content = content[11:]
        elif content.startswith("```") and not content.endswith("```"):
            logger.warning("Markdown code block not closed")
            content = content[3:]

        return content.strip()
