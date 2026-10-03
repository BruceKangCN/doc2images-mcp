"""doc2images-mcp: render documents to images for multimodal models.

This server performs deterministic "document -> image" conversion only. It does
not convert documents to Markdown and does not do LLM-based document
understanding.

PDF rendering is delegated to pypdfium2 (PDFium), which ships its own encoding
data (including the CJK CMaps) and needs no external binaries.
"""

from fastmcp import FastMCP
from fastmcp.utilities.types import Image

from doc2images_mcp.util import render_pdf, resolve

MIN_DPI = 72
MAX_DPI = 2400
DEFAULT_DPI = 150
DEFAULT_MAX_PAGES = 10
HARD_MAX_PAGES = 50
DEFAULT_MAX_WIDTH = 3000

mcp = FastMCP(
    "doc2images",
    instructions=(
        "Convert documents into images and return them as multimodal content. "
        "Use dpi, first_page, last_page and max_pages to control how much of "
        "the document is sent to the model. Prefer small page ranges."
    ),
)


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

    path = resolve(file_path)
    return render_pdf(path, dpi, first_page, last_page, max_pages, max_width)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
