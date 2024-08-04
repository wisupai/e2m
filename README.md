# e2m
Everything to Markdown.

# Demo

## Install

```bash
pip install wisup_e2m
```

## Demo

```python
from wisup_e2m import PdfParser
from wisup_e2m.parsers.base import BaseParserConfig

pdf_parser = PdfParser(
    BaseParserConfig(engine="unstructured", langs=["en"])
)

parsed_data = pdf_parser.get_parsed_data(
    "sample.pdf",
    include_image_link_in_text=True,
    work_dir="./out",
    image_dir="./out/figures",
    relative_path=True
)

print(parsed_data.text)
```
