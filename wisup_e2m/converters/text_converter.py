from wisup_e2m.converters.base import BaseConverter

_text_converter_params = [
    "text",
    "verbose",
    "strategy",
]


class TextConverter(BaseConverter):
    SUPPORTED_ENGINES = ["litellm", "zhipuai"]

    def _convert_to_md_by_litellm(
        self, text: str, verbose: bool = True, strategy: str = "default", **kwargs
    ) -> str:
        from wisup_e2m.converters.strategies.litellm_strategy import LitellmStrategy

        litellm_strategy = LitellmStrategy()

        if strategy == "default":
            return litellm_strategy.default_text_convert(
                text, verbose=verbose, **self.config.to_dict()
            )
        elif strategy == "with_toc":
            return litellm_strategy.with_toc_text_convert(
                text, verbose=verbose, **self.config.to_dict()
            )
        else:
            raise ValueError(f"Unsupported strategy: {strategy}")

    def _convert_to_md_by_zhipuai(
        self, text: str, verbose: bool = True, strategy: str = "default", **kwargs
    ) -> str:
        from wisup_e2m.converters.strategies.zhipuai_strategy import ZhipuaiStrategy

        zhipuai_strategy = ZhipuaiStrategy(zhipuai_client=self.zhipuai_client)

        if strategy == "default":
            return zhipuai_strategy.default_text_convert(
                text, verbose=verbose, **self.config.to_dict()
            )
        elif strategy == "with_toc":
            return zhipuai_strategy.with_toc_text_convert(
                text, verbose=verbose, **self.config.to_dict()
            )
        else:
            raise ValueError(f"Unsupported strategy: {strategy}")

    def convert(
        self,
        text: str,
        verbose: bool = True,
        strategy: str = "default",
        **kwargs,
    ) -> str:
        for k, v in locals().items():
            if k in _text_converter_params:
                kwargs[k] = v

        if self.config.engine == "litellm":
            return self._convert_to_md_by_litellm(**kwargs)
        elif self.config.engine == "zhipuai":
            return self._convert_to_md_by_zhipuai(**kwargs)
        else:
            raise ValueError(f"Unsupported engine: {self.config.engine}")
