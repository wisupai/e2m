# E2M

<p align="center">
    <a href="https://github.com/wisupai/e2m">
        <img src="https://img.shields.io/badge/e2m-repo-blue" alt="E2M Repo">
    </a>
    <a href="https://github.com/Jing-yilin/E2M/tags/0.1.2">
        <img src="https://img.shields.io/badge/version-0.1.2-blue" alt="E2M Version">
    </a>
    <a href="https://www.python.org/downloads/">
        <img src="https://img.shields.io/badge/python-3.10%20%7C%203.11-blue" alt="Python Version">
    </a>
</p>

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

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or inquiries, please open an issue on [GitHub](https://github.com/wisupai/e2m) or contact us at [team@wisup.ai](mailto:team@wisup.ai).
