"""doc2images-mcp: render documents to images for multimodal models.

This server performs deterministic "document -> image" conversion only. It does
not convert documents to Markdown and does not do LLM-based document
understanding.

PDF rendering is delegated to pypdfium2 (PDFium), which ships its own encoding
data (including the CJK CMaps) and needs no external binaries.
"""

import io
import os
from pathlib import Path

import pypdfium2 as pdfium
from fastmcp import FastMCP
from fastmcp.utilities.types import Image
from PIL import Image as PILImage

mcp = FastMCP(
    "doc2images",
    instructions=(
        "Convert documents into images and return them as multimodal content. "
        "Use dpi, first_page, last_page and max_pages to control how much of "
        "the document is sent to the model. Prefer small page ranges."
    ),
)

# Base directory for resolving relative paths. Override with DOC2IMG_BASE_DIR.
BASE_DIR = Path(os.environ.get("DOC2IMG_BASE_DIR", os.getcwd())).expanduser().resolve()

MIN_DPI = 72
MAX_DPI = 2400
DEFAULT_DPI = 150
DEFAULT_MAX_PAGES = 10
HARD_MAX_PAGES = 50
DEFAULT_MAX_WIDTH = 3000

# PDFium's default rendering scale is 1.0 at 72 dpi.
PDFIUM_SCALE_BASE = 72.0


def _resolve(path: str) -> Path:
    """Resolve ``path``, interpreting relative paths against ``BASE_DIR``."""
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = BASE_DIR / p
    p = p.resolve()
    if not p.is_file():
        raise ValueError(f"Not a file: {p}")
    return p


def _to_png(image: PILImage.Image, max_width: int) -> bytes:
    """Downscale if needed, then encode as PNG bytes."""
    if image.width > max_width:
        ratio = max_width / image.width
        new_size = (max_width, max(1, round(image.height * ratio)))
        image = image.resize(new_size, PILImage.Resampling.LANCZOS)
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _render_pdf(
    path: Path,
    dpi: int,
    first_page: int,
    last_page: int,
    max_pages: int,
    max_width: int,
) -> list[Image]:
    try:
        with pdfium.PdfDocument(path) as pdf:
            scale = dpi / PDFIUM_SCALE_BASE
            start = first_page - 1
            end = min(start + max_pages, len(pdf))
            if last_page and last_page > 0:
                end = min(end, last_page)
            return _render_pages_to_images(pdf, scale, start, end, max_width)
    except pdfium.PdfiumError as exc:
        raise ValueError(f"Failed to open PDF: {path}") from exc


def _render_pages_to_images(
    pdf: pdfium.PdfDocument,
    scale: float,
    start_index: int,
    end_index: int,
    max_width: int,
) -> list[Image]:
    images: list[Image] = []
    for i in range(start_index, end_index):
        # `scale` is of type `float`, but some language servers (e.g. Pyright)
        # infer incorrect type information (`int`) from the default value.
        bitmap: pdfium.PdfBitmap = pdf[i].render(scale=scale)  # type: ignore
        image = Image(data=_to_png(bitmap.to_pil(), max_width), format="png")
        images.append(image)
    return images


@mcp.tool()
def pdf_to_images(
    file_path: str,
    dpi: int = DEFAULT_DPI,
    first_page: int = 1,
    last_page: int = 0,
    max_pages: int = DEFAULT_MAX_PAGES,
    max_width: int = DEFAULT_MAX_WIDTH,
) -> list[Image]:
    """Render document pages to images.

    Returns one image per page. Use first_page/last_page/max_pages to limit how
    much of the document is sent to the model.

    Args:
        file_path: Path to the document. Relative paths resolve against
            DOC2IMG_BASE_DIR (defaults to the current working directory).
        dpi: Rasterisation resolution, 72-2400. Higher is sharper but larger.
        first_page: 1-based first page to render.
        last_page: 1-based last page to render; 0 means "until max_pages".
        max_pages: Hard cap on the number of pages returned (1-50).
        max_width: Maximum output width in pixels; wider pages are scaled down.
    """
    if not MIN_DPI <= dpi <= MAX_DPI:
        raise ValueError(f"dpi must be between {MIN_DPI} and {MAX_DPI}, got {dpi}")
    if first_page < 1:
        raise ValueError(f"first_page must be >= 1, got {first_page}")
    if 0 < last_page < first_page:
        raise ValueError(
            f"last_page ({last_page}) must be >= first_page ({first_page}) or 0"
        )
    if not 1 <= max_pages <= HARD_MAX_PAGES:
        raise ValueError(
            f"max_pages must be between 1 and {HARD_MAX_PAGES}, got {max_pages}"
        )
    if max_width < 1:
        raise ValueError(f"max_width must be >= 1, got {max_width}")

    path = _resolve(file_path)
    return _render_pdf(path, dpi, first_page, last_page, max_pages, max_width)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
