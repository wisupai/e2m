<p align="center">
  <img src="docs/images/wisup_e2m_banner.jpg" width="800px" alt="wisup_e2m Logo">
</p>

<p align="center">
    <a href="https://github.com/wisupai/e2m">
        <img src="https://img.shields.io/badge/e2m-repo-blue" alt="E2M 代码仓库">
    </a>
    <a href="https://github.com/Jing-yilin/E2M/tags/0.1.4">
        <img src="https://img.shields.io/badge/version-0.1.4-blue" alt="E2M 版本">
    </a>
    <a href="https://www.python.org/downloads/">
        <img src="https://img.shields.io/badge/python-3.10%20%7C%203.11-blue" alt="Python 版本">
    </a>
</p>

# 🚀 E2M: Everything to Markdown

**Everything to Markdown**

E2M 是一个多功能工具，可将各种文件类型转换为 Markdown 格式。

## 📂 支持的文件类型

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

## 📦 安装

使用 pip 安装 E2M：

```bash
pip install wisup_e2m
```

## ⚡️ 解析器: 快速开始

以下是使用 E2M 解析器的简单示例：

### 📄 PDF 解析器

```python
from wisup_e2m import PdfParser

pdf_path = "./test.pdf"
parser = PdfParser(engine="marker") # pdf 引擎: marker, unstructured, surya_layout
pdf_data = parser.parse(pdf_path)
print(pdf_data.text)
```

### 📝 DOC 解析器

```python
from wisup_e2m import DocParser

doc_path = "./test.doc"
parser = DocParser(engine="unstructured") # doc 引擎: unstructured
doc_data = parser.parse(doc_path)
print(doc_data.text)
```

### 📜 DOCX 解析器

```python
from wisup_e2m import DocxParser

docx_path = "./test.docx"
parser = DocxParser(engine="unstructured") # docx 引擎: unstructured
docx_data = parser.parse(docx_path)
print(docx_data.text)
```

### 📚 EPUB 解析器

```python
from wisup_e2m import EpubParser

epub_path = "./test.epub"
parser = EpubParser(engine="unstructured") # epub 引擎: unstructured
epub_data = parser.parse(epub_path)
print(epub_data.text)
```

### 🌐 HTML 解析器

```python
from wisup_e2m import HtmlParser

html_path = "./test.html"
parser = HtmlParser(engine="unstructured") # html 引擎: unstructured
html_data = parser.parse(html_path)
print(html_data.text)
```

### 🔗 URL 解析器

```python
from wisup_e2m import UrlParser

url = "https://www.example.com"
parser = UrlParser(engine="jina") # url 引擎: jina
url_data = parser.parse(url)
print(url_data.text)
```

### 🖼️ PPT 解析器

```python
from wisup_e2m import PptParser

ppt_path = "./test.ppt"
parser = PptParser(engine="unstructured") # ppt 引擎: unstructured
ppt_data = parser.parse(ppt_path)
print(ppt_data.text)
```

### 🖼️ PPTX 解析器

```python
from wisup_e2m import PptxParser

pptx_path = "./test.pptx"
parser = PptxParser(engine="unstructured") # pptx 引擎: unstructured
pptx_data = parser.parse(pptx_path)
print(pptx_data.text)
```

### 🎤 语音解析器

```python
from wisup_e2m import VoiceParser

voice_path = "./test.mp3"
parser = VoiceParser(
  engine="openai_whisper_local", # 语音引擎: openai_whisper_api, openai_whisper_local
  model="large" # 可用模型: https://github.com/openai/whisper#available-models-and-languages
  )

voice_data = parser.parse(voice_path)
print(voice_data.text)
```

## 🔄 转换器: 快速开始

以下是使用 E2M 转换器的简单示例：

### 📝 文本转换器

```python
from wisup_e2m import TextConverter

text = "从任何解析器解析的文本数据"
converter = TextConverter(
  engine="litellm", # 文本引擎: litellm
  model="deepseek/deepseek-chat",
  api_key="你的 API 密钥",
  base_url="你的基础 URL"
  )
text_data = converter.convert(text)
print(text_data)
```

### 🖼️ 图片转换器

```python
from wisup_e2m import ImageConverter

images = ["./test1.png", "./test2.png"]
converter = ImageConverter(
  engine="litellm", # 图片引擎: litellm
  model="gpt-4o",
  api_key="你的 API 密钥",
  base_url="你的基础 URL"
  )
image_data = converter.convert(images)
print(image_data)
```

## 🆙 下一步

### 🛠️ E2MParser

`E2MParser` 是一个集成解析器，支持多种文件类型。可以将各种文件类型解析为 Markdown 格式。

```python
from wisup_e2m import E2MParser

# 使用配置文件初始化解析器
ep = E2MParser.from_config("config.yaml")

# 解析指定文件
data = ep.parse(file_name="/path/to/file.pdf")

# 将解析的数据以字典格式打印
print(data.to_dict())
```

### 🛠️ E2MConverter

`E2MConverter` 是一个集成转换器，支持文本和图片转换。可以将文本和图片转换为 Markdown 格式。

```python
from wisup_e2m import E2MConverter

ec = E2MConverter.from_config("./config.yaml")

text = "从任何解析器解析的文本数据"

ec.convert(text=text)

images = ["test.jpg", "test.png"]
ec.convert(images=images)
```

你可以使用 `config.yaml` 文件来指定要使用的解析器和转换器。以下是一个 `config.yaml` 文件的示例：

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
        # 选项1: 使用 openai whisper API
        # engine: "openai_whisper_api"
        # api_base: "https://api.openai.com/v1"
        # api_key: "你的 API 密钥"
        # model: "whisper"

        # 选项2: 使用本地 whisper 模型
        engine: "openai_whisper_local"
        model: "large" # 可用模型: https://github.com/openai/whisper#available-models-and-languages

converter:
    text_converter:
        engine: "litellm"
        model: "deepseek/deepseek-chat"
        api_key: "你的 API 密钥"
        # base_url: ""
    image_converter:
        engine: "litellm"
        model: "gpt-4o-mini"
        api_key: "你的 API 密钥"
        # base_url: ""
```

## ❓ 问答

-   未找到资源 wordnet。
    -   完全卸载 `nltk`：`pip uninstall nltk`
    -   使用以下命令重新安装 `nltk`：`pip install nltk`
    -   手动下载 [corpora/wordnet.zip](https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/wordnet.zip) 并将其解压缩到错误消息中指定的目录。或者，您可以使用以下命令下载：
        -   Windows: `wget https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/wordnet.zip -O ~\AppData\Roaming\nltk_data\corpora\wordnet.zip` 并 `unzip ~\AppData\Roaming\nltk_data\corpora\wordnet.zip -d ~\AppData\Roaming\nltk_data\corpora\`
        -   Unix: `wget https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/wordnet.zip -O ~/nltk_data/corpora/wordnet.zip` 并 `unzip ~/nltk_data/corpora/wordnet.zip -d ~/nltk_data/corpora/`

## 📜 许可证

此项目基于 MIT 许可证。详情请参见 [LICENSE](LICENSE) 文件。

## 📧 联系我们

扫描以下二维码加入我们的微信群(备注来自e2m项目):

<p align="center">
  <img src="docs/images/wechat_QR.jpg" width="200px" alt="wisup_e2m Logo">
</p>

如有任何问题或疑问，请在 [GitHub](https://github.com/wisupai/e2m) 上创建 issue 或通过 [team@wisup.ai](mailto:team@wisup.ai) 联系我们。

## 🌟 贡献

<a href="https://github.com/wisupai/e2m/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=wisupai/e2m" />
</a>