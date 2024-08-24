from typing import Dict, List

from wisup_e2m.converters.base import BaseConverter

_image_converter_params = [
    "images",
    "attached_images_map",
    "verbose",
    "strategy",
    "image_batch_size",
]


class ImageConverter(BaseConverter):
    SUPPORTED_ENGINES = ["litellm", "zhipuai"]

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

    def _convert_to_md_by_zhipuai(
        self,
        images: List[str],
        attached_images_map: Dict[str, List[str]] = {},
        verbose: bool = True,
        strategy: str = "default",
        image_batch_size: int = 5,
        **kwargs,
    ) -> str:
        from wisup_e2m.converters.strategies.zhipuai_strategy import ZhipuaiStrategy

        zhipuai_strategy = ZhipuaiStrategy(self.zhipuai_client)

        if strategy == "default":
            return zhipuai_strategy.default_image_convert(
                images=images,
                attached_images_map=attached_images_map,
                verbose=verbose,
                image_batch_size=image_batch_size,
                **self.config.to_dict(),
            )
        elif strategy == "with_toc":
            return zhipuai_strategy.with_toc_image_convert(
                images=images,
                attached_images_map=attached_images_map,
                verbose=verbose,
                image_batch_size=image_batch_size,
                **self.config.to_dict(),
            )
        else:
            raise ValueError(f"Unsupported strategy: {strategy}")

    def convert(
        self,
        images: List[str],
        attached_images_map: Dict[str, List[str]] = {},
        verbose: bool = True,
        strategy: str = "default",
        image_batch_size: int = 5,
        **kwargs,
    ) -> str:
        for k, v in locals().items():
            if k in _image_converter_params:
                kwargs[k] = v

        if self.config.engine == "litellm":
            return self._convert_to_md_by_litellm(**kwargs)
        elif self.config.engine == "zhipuai":
            return self._convert_to_md_by_zhipuai(**kwargs)
        else:
            raise ValueError(f"Unsupported engine: {self.config.engine}")
