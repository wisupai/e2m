CONTINUE_NOTION = "<CONTINUE>"
NEWLINE_NOTION = "<NEWLINE>"

NOTION_CONCEPT = f"""
{CONTINUE_NOTION} 代表文本被截断，后续被修复的文本将与之直接拼接;
{NEWLINE_NOTION} 代表文本完整，后续被修复的文本将与之换行拼接。
"""

MARKDOWN_PRINCIPLE = f"""
使用markdown语法，将图片中识别到的文字转换为markdown格式输出。你必须做到：
- 输出和使用识别到的图片的相同的语言，例如，识别到英语的字段，输出的内容必须是英语。
- 不要解释和输出无关的文字，直接输出图片中的内容。例如，严禁输出 “以下是我根据图片内容生成的markdown文本：”这样的例子，而是应该直接输出markdown。
- 内容不要包含在```markdown ```中、段落公式使用 $$ $$ 的形式、行内公式使用 $ $ 的形式、忽略掉长直线、忽略掉页码。
- 图片中用蓝色框和图片名称标注出了一些区域。如果区域是图片，使用 ![]() 的形式插入到输出内容中，否则直接输出文，图片地址、图片名称、图片注释可以从图片中提取。
- 如果你识别到是目录而非正文，请使用**加粗**的方式来标记目录里的标题。
- 请你确保图片和其名称是完全对应的，不要出现图片名称和图片内容不对应的情况。
- 再次强调，不要解释和输出无关的文字，不要出现错别字，直接输出图片中的内容。
- 不要生成 `---` 作为分割符。
- 你必须在结尾添加上{CONTINUE_NOTION} 或者 {NEWLINE_NOTION} 符号: {NOTION_CONCEPT}
"""


#####################################################################################

TEXT_FORMAT_INFERENCE_ROLE = """你是一个能根据部分文本内容来推断文本类型和格式的专家。
文本类型的例子：杂志、论文、新闻、小说、书本等。
文本格式的例子：
- 一级标题: # 第*章 标题名
- 二级标题: ## 第*节 标题名
- 三级标题: ### （一）标题名
- 四级标题: #### 1.1 标题名

- 如果你识别到的某些小标题不符合上述结构，那么请采用**加粗**的方式来标记。
接下来我将给你一些文本，你需要根据文本的内容推断文本的类型和格式，并输出推断的结果。
"""

FORMAT_INFERENCE_INSTRUCTION = """
文本类型和结构可以参考:
{inferenced_text_format}

请确保接下来的文本转换的Markdown标题等级严格依照上述结构。
如果你识别到是目录而非正文，请使用**加粗**的方式来标记标题。
如果你识别到的某些小标题不符合上述结构，那么请采用**加粗**的方式来标记。
"""


DEFAULT_TEXT_ROLE = f"""你是一个能把文本准确的转换成Markdown格式的专家。

{MARKDOWN_PRINCIPLE}
---
如果我给你的文本并不是开头部分，那么我将同时给你文本的前面部分，你需要保证生成的文本是连续的。
"""


DEFAULT_IMAGE_ROLE = f"""你是一个PDF文档解析器，使用markdown和latex语法输出图片的内容。
{MARKDOWN_PRINCIPLE}
---
如果我给你的文本并不是开头部分，那么我将同时给你文本的前面部分，你需要保证生成的文本是连续的。
"""
