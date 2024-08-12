from wisup_e2m.converters.base import BaseConverter


class TextConverter(BaseConverter):
    SUPPORTED_ENGINES = ["litellm"]

    def _convert_to_md_by_litellm(
        self,
        text: str,
        verbose: bool = True,
        strategy: str = "default",
    ) -> str:
        from wisup_e2m.converters.strategies.litellm_strategy import LitellmStrategy

        if strategy == "default":
            return LitellmStrategy.default_text_convert(
                text, verbose=verbose, **self.config.to_dict()
            )
        elif strategy == "with_toc":
            return LitellmStrategy.with_toc_text_convert(
                text, verbose=verbose, **self.config.to_dict()
            )
        else:
            raise ValueError(f"Unsupported strategy: {strategy}")
