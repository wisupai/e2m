from e2m import PdfParser
from e2m.parsers.base import BaseParserConfig

from pathlib import Path
import json
import logging

logging.basicConfig(level=logging.INFO)

pdf_parser = PdfParser(
    BaseParserConfig(engine="marker", langs=["en"])
)

pwd = Path.cwd()
file =pwd/"Attention is All You Need Paper.pdf"
file_name = file.stem.replace(" ", "_")
print(file_name)
work_dir = pwd / f"marker_{file_name}"
image_dir = work_dir / "figures"
parsed_data_file = work_dir / f"parsed_data_{file_name}.json"
parsed_text_file = work_dir / f"parsed_text_{file_name}.md"

work_dir.mkdir(parents=True, exist_ok=True)

parsed_data = pdf_parser.get_parsed_data(
    str(file),
    start_page=2,
    end_page=3,
    include_image_link_in_text=True,
    image_dir=str(image_dir),
    work_dir=str(work_dir),
    relative_path=True
)

# # save parsed_data
# with open(os.path.join(work_dir, f"{file_name}_marker.md"), "w") as f:
#     f.write(parsed_data.text)

json.dump(parsed_data.to_dict(), open(parsed_data_file, "w"), indent=4)
print(f"parsed_data saved to {parsed_data_file}")

text = parsed_data.text
# save to a file
with open(parsed_text_file, "w") as f:
    f.write(text)
print(f"parsed_data text saved to {parsed_text_file}")
