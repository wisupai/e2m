import importlib

from wisup_e2m.parsers.base import BaseParser


def load_class(class_type):
    module_path, class_name = class_type.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


class ParserFactory:
    provider_to_class = {
        "pdf_parser": "wisup_e2m.parsers.doc.pdf_parser.PdfParser",
        "html_parser": "wisup_e2m.parsers.doc.html_parser.HtmlParser",
        "url_parser": "wisup_e2m.parsers.doc.url_parser.UrlParser",
        "pptx_parser": "wisup_e2m.parsers.doc.pptx_parser.PptxParser",
        "ppt_parser": "wisup_e2m.parsers.doc.ppt_parser.PptParser",
        "epub_parser": "wisup_e2m.parsers.doc.epub_parser.EpubParser",
        "docx_parser": "wisup_e2m.parsers.doc.docx_parser.DocxParser",
        "doc_parser": "wisup_e2m.parsers.doc.doc_parser.DocParser",
        "voice_parser": "wisup_e2m.parsers.aud.voice_parser.VoiceParser",
    }

    provider_to_config = {
        "pdf_parser": "wisup_e2m.configs.parsers.pdf_parser_config.PdfParserConfig",
        "html_parser": "wisup_e2m.configs.parsers.html_parser_config.HtmlParserConfig",
        "url_parser": "wisup_e2m.configs.parsers.url_parser_config.UrlParserConfig",
        "pptx_parser": "wisup_e2m.configs.parsers.pptx_parser_config.PptxParserConfig",
        "ppt_parser": "wisup_e2m.configs.parsers.ppt_parser_config.PptParserConfig",
        "epub_parser": "wisup_e2m.configs.parsers.epub_parser_config.EpubParserConfig",
        "docx_parser": "wisup_e2m.configs.parsers.docx_parser_config.DocxParserConfig",
        "doc_parser": "wisup_e2m.configs.parsers.doc_parser_config.DocParserConfig",
        "voice_parser": "wisup_e2m.configs.parsers.voice_parser_config.VoiceParserConfig",
    }

    @classmethod
    def create(cls, provider_name, config) -> BaseParser | None:
        class_type = cls.provider_to_class.get(provider_name)
        config_type = cls.provider_to_config.get(provider_name)
        if class_type:
            parser_instance = load_class(class_type)
            config_instance = load_class(config_type)
            base_config = config_instance(**config)
            return parser_instance(base_config)
        else:
            raise ValueError(f"Unsupported Parser provider: {provider_name}")


class ConverterFactory:
    provider_to_class = {
        "text_converter": "wisup_e2m.converters.text_converter.TextConverter",
        "image_converter": "wisup_e2m.converters.image_converter.ImageConverter",
    }

    provider_to_config = {
        "text_converter": "wisup_e2m.configs.converters.text_converter_config.TextConverterConfig",
        "image_converter": "wisup_e2m.configs.converters.image_converter_config.ImageConverterConfig",
    }

    @classmethod
    def create(cls, provider_name, config):
        class_type = cls.provider_to_class.get(provider_name)
        config_type = cls.provider_to_config.get(provider_name)
        if class_type:
            converter_instance = load_class(class_type)
            config_instance = load_class(config_type)
            base_config = config_instance(**config)
            return converter_instance(base_config)
        else:
            raise ValueError(f"Unsupported Converter provider: {provider_name}")
