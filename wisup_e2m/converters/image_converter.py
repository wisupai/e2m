from wisup_e2m.converters.base import BaseConverter
from typing import List, Dict


class ImageConverter(BaseConverter):
    SUPPORTED_ENGINES = ["litellm"]

    def _convert_to_md_by_litellm(
        self,
        images: List[str],
        attached_images_map: Dict[str, List[str]] = {},
        verbose: bool = True,
        strategy: str = "default",
        image_batch_size: int = 5,
        **kwargs,
    ) -> str:
        from wisup_e2m.converters.strategies.litellm_strategy import LitellmStrategy

        if strategy == "default":
            return LitellmStrategy().default_image_convert(
                images=images,
                attached_images_map=attached_images_map,
                verbose=verbose,
                image_batch_size=image_batch_size,
                **self.config.to_dict(),
            )
        elif strategy == "with_toc":
            return LitellmStrategy().with_toc_image_convert(
                images=images,
                attached_images_map=attached_images_map,
                verbose=verbose,
                image_batch_size=image_batch_size,
                **self.config.to_dict(),
            )
        else:
            raise ValueError(f"Unsupported strategy: {strategy}")
