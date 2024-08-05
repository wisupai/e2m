# e2m

Everything to Markdown.

## Install

```bash
pip install wisup_e2m
```

## Demo

```python
from wisup_e2m import E2MParser

ep = E2MParser.from_config("config.yaml")
data = ep.parse(file_name="/path/to/file.pdf")

print(data.to_dict())
```
