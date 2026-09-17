import base64
import mimetypes
from pathlib import Path
from typing import Union

from langchain_core.messages import HumanMessage

from app.utils.llm import get_vision_llm


def ocr_image(image_bytes: bytes, filename: str = "image.png") -> str:
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type or not mime_type.startswith("image/"):
        mime_type = "image/png"

    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64}"

    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": (
                    "请仔细识别图片中的所有文字内容，并按原始排版顺序输出。"
                    "保留标题、段落、列表等结构。不要添加任何解释或评论，"
                    "只输出识别到的文字内容。"
                ),
            },
            {"type": "image_url", "image_url": {"url": data_url}},
        ]
    )

    llm = get_vision_llm()
    response = llm.invoke([message])
    return response.content.strip()
