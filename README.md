<p align="center">
  <img src="docs/images/wisup_e2m_banner.jpg" width="800px" alt="wisup_e2m Logo">
</p>

<p align="center">
    <a href="https://github.com/wisupai/e2m">
        <img src="https://img.shields.io/badge/e2m-repo-blue" alt="E2M Repo">
    </a>
    <a href="https://github.com/Jing-yilin/E2M/tags/0.1.3">
        <img src="https://img.shields.io/badge/version-0.1.2-blue" alt="E2M Version">
    </a>
    <a href="https://www.python.org/downloads/">
        <img src="https://img.shields.io/badge/python-3.10%20%7C%203.11-blue" alt="Python Version">
    </a>
</p>

# E2M: Everything to Markdown

**Everything to Markdown**

E2M is a versatile tool that converts a wide range of file types into Markdown format.

## Supported File Types

-   doc
-   docx
-   epub
-   html
-   htm
-   url
-   pdf
-   pptx
-   mp3
-   m4a

## Installation

To install E2M, use pip:

```bash
pip install wisup_e2m
```

## Usage

Here's a simple example demonstrating how to use E2M:

```python
from wisup_e2m import E2MParser

# Initialize the parser with your configuration file
ep = E2MParser.from_config("config.yaml")

# Parse the desired file
data = ep.parse(file_name="/path/to/file.pdf")

# Print the parsed data as a dictionary
print(data.to_dict())
```

## Config Template

```yaml
parsers:
  doc_parser:
    engine: "unstructured"
    langs: ["en", "zh"]
  docx_parser:
    engine: "unstructured"
    langs: ["en", "zh"]
  epub_parser:
    engine: "unstructured"
    langs: ["en", "zh"]
  html_parser:
    engine: "unstructured"
    langs: ["en", "zh"]
  url_parser:
    engine: "jina"
    langs: ["en", "zh"]
  pdf_parser:
    engine: "marker"
    langs: ["en", "zh"]
  pptx_parser:
    engine: "unstructured"
    langs: ["en", "zh"]
  voice_parser:
    # option 1: use openai whisper api
    # engine: "openai_whisper_api"
    # api_base: "https://api.openai.com/v1"
    # api_key: "your_api_key"
    # model: "whisper"

    # option 2: use local whisper model
    engine: "openai_whisper_local"
    model: "large" # available models: https://github.com/openai/whisper#available-models-and-languages

converter:
  text_converter:
    engine: "litellm"
    model: "deepseek/deepseek-chat"
    api_key: "your_api_key"
    # base_url: ""
  image_converter:
    engine: "litellm"
    model: "gpt-4o-mini"
    api_key: "your_api_key"
    # base_url: ""

```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or inquiries, please open an issue on [GitHub](https://github.com/wisupai/e2m) or contact us at [team@wisup.ai](mailto:team@wisup.ai).

## 🌟Contributing

<a href="https://github.com/wisupai/e2m/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=wisupai/e2m" />
</a>
