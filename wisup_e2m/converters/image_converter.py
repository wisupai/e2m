from wisup_e2m.converters.base import BaseConverter
from typing import List


class ImageConverter(BaseConverter):

    def convert_to_md(self, images: List[str], verbose: bool = True, **kwargs) -> str:
        if self.config.engine == "litellm":
            return self._convert_to_md_by_litellm(images=images, verbose=verbose)
        else:
            raise ValueError(f"Unsupported engine: {self.config.engine}")
