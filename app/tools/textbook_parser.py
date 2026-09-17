import io
from pathlib import Path
from typing import Union

from app.tools.image_ocr import ocr_image


_TEXT_SUFFIXES = {".txt", ".md"}
_PDF_SUFFIXES = {".pdf"}
_DOCX_SUFFIXES = {".docx", ".doc"}
_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}

_TEXT_ENCODINGS = ("utf-8-sig", "utf-8", "gbk", "gb18030", "utf-16", "big5")


def parse_textbook(file_path: Union[str, Path]) -> str:
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix in _PDF_SUFFIXES:
        return _parse_pdf(file_path)
    elif suffix in _DOCX_SUFFIXES:
        return _parse_docx(file_path)
    elif suffix in _TEXT_SUFFIXES:
        return _parse_text(file_path)
    elif suffix in _IMAGE_SUFFIXES:
        return ocr_image(file_path.read_bytes(), file_path.name)
    else:
        raise ValueError(
            f"不支持的文件格式: {suffix}，"
            f"仅支持 {sorted(_TEXT_SUFFIXES | _PDF_SUFFIXES | _DOCX_SUFFIXES | _IMAGE_SUFFIXES)}"
        )


def parse_textbook_bytes(content: bytes, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in _PDF_SUFFIXES:
        return _parse_pdf_bytes(content)
    elif suffix in _TEXT_SUFFIXES:
        return _decode_text_bytes(content)
    elif suffix in _IMAGE_SUFFIXES:
        return ocr_image(content, filename)
    elif suffix in _DOCX_SUFFIXES:
        return _parse_docx_bytes(content)
    else:
        raise ValueError(
            f"不支持的文件格式: {suffix}，"
            f"仅支持 {sorted(_TEXT_SUFFIXES | _PDF_SUFFIXES | _DOCX_SUFFIXES | _IMAGE_SUFFIXES)}"
        )


def _parse_pdf(file_path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(file_path))
    return _extract_pdf_text(reader)


def _parse_pdf_bytes(content: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    return _extract_pdf_text(reader)


def _extract_pdf_text(reader) -> str:
    pages_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages_text.append(text.strip())
    return "\n".join(pages_text)


def _parse_docx(file_path: Path) -> str:
    return _extract_docx_text(file_path)


def _parse_docx_bytes(content: bytes) -> str:
    return _extract_docx_text(io.BytesIO(content))


def _extract_docx_text(source) -> str:
    from docx import Document

    doc = Document(source)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def _parse_text(file_path: Path) -> str:
    return _decode_text_bytes(file_path.read_bytes())


def _decode_text_bytes(content: bytes) -> str:
    for enc in _TEXT_ENCODINGS:
        try:
            return content.decode(enc).strip()
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError("无法识别文本文件编码，请将文件保存为 UTF-8 编码后重试")
