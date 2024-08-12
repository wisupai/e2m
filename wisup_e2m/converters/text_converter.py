from wisup_e2m.converters.base import BaseConverter


class TextConverter(BaseConverter):

    def convert_to_md(self, text: str, verbose: bool = True, **kwargs) -> str:
        if self.config.engine == "litellm":
            return self._convert_to_md_by_litellm(text=text, verbose=verbose)
        else:
            raise ValueError(f"Unsupported engine: {self.config.engine}")
