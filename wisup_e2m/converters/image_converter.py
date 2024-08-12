from wisup_e2m.converters.base import BaseConverter
from typing import List


class ImageConverter(BaseConverter):
    SUPPORTED_ENGINES = ["litellm"]

    def _convert_to_md_by_litellm(
        self,
        images: List[str],
        verbose: bool = True,
        strategy: str = "default",
    ) -> str:
        from wisup_e2m.converters.strategies.litellm_strategy import LitellmStrategy

        if strategy == "default":
            return LitellmStrategy.default_image_convert(
                images, verbose=verbose, **self.config.to_dict()
            )
        elif strategy == "with_toc":
            return LitellmStrategy.with_toc_image_convert(
                images, verbose=verbose, **self.config.to_dict()
            )
        else:
            raise ValueError(f"Unsupported strategy: {strategy}")
