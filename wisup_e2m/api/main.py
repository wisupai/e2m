from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi import HTTPException
from typing import Optional, List
from pathlib import Path
import logging

from wisup_e2m.api.models import (
    ParseRequest,
    ParseResponse,
    ConvertRequest,
    ConvertResponse,
)
from wisup_e2m.converters.base import ConvertHelpfulInfo
from wisup_e2m.api.services import parse_file_service, convert_data_service
from wisup_e2m.api.dependencies import get_parser, get_converter

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
pwd = Path(__file__).parent.resolve()
static_dir = str(pwd / "static")

# 创建 FastAPI 实例
app = FastAPI(
    title="E2M API",
    description="API for converting various file formats to Markdown using different parsers and converters.",
    version="0.1.63",
)

# 添加静态文件中间件
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/parse/", response_model=ParseResponse)
async def parse_file(
    file: UploadFile = File(...),
    url: Optional[str] = Form(None),
    start_page: Optional[int] = Form(None),
    end_page: Optional[int] = Form(None),
    extract_images: bool = Form(True),
    include_image_link_in_text: bool = Form(True),
    relative_path: bool = Form(True),
    work_dir: str = Form("./"),
    image_dir: str = Form("./figures"),
    include_page_breaks: bool = Form(False),
    include_slide_notes: bool = Form(False),
    ignore_transparent_images: bool = Form(True),
    parser=Depends(get_parser),
):
    request = ParseRequest(
        url=url,
        start_page=start_page,
        end_page=end_page,
        extract_images=extract_images,
        include_image_link_in_text=include_image_link_in_text,
        relative_path=relative_path,
        work_dir=work_dir,
        image_dir=image_dir,
        include_page_breaks=include_page_breaks,
        include_slide_notes=include_slide_notes,
        ignore_transparent_images=ignore_transparent_images,
    )
    return await parse_file_service(file, request, parser)


@app.post("/convert/", response_model=ConvertResponse)
async def convert_data(
    text: Optional[str] = Form(None),
    images: Optional[List[str]] = Form(None),
    strategy: Optional[str] = Form("default"),
    image_batch_size: Optional[int] = Form(5),
    convert_helpful_info: ConvertHelpfulInfo = Depends(ConvertHelpfulInfo),
    converter=Depends(get_converter),
):
    request = ConvertRequest(
        text=text,
        images=images,
        strategy=strategy,
        image_batch_size=image_batch_size,
        convert_helpful_info=convert_helpful_info,
    )
    try:
        converted_text = await convert_data_service(request, converter)
        return ConvertResponse(converted_text=converted_text)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error in convert_data: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <html>
        <head>
            <title>E2M API</title>
            <link rel="icon" type="image/x-icon" href="/static/favicon.ico">
        </head>
        <body>
            <h1>Welcome to E2M API</h1>
        </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
