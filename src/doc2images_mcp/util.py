import io
import os
from pathlib import Path

import pypdfium2 as pdfium
from fastmcp.utilities.types import Image
from PIL import Image as PILImage

# Base directory for resolving relative paths. Override with DOC2IMG_BASE_DIR.
BASE_DIR = Path(os.environ.get("DOC2IMG_BASE_DIR", os.getcwd())).expanduser().resolve()

# PDFium's default rendering scale is 1.0 at 72 dpi.
PDFIUM_SCALE_BASE = 72.0


def resolve(path: str) -> Path:
    """Resolve ``path``, interpreting relative paths against ``BASE_DIR``."""
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = BASE_DIR / p
    p = p.resolve()
    if not p.is_file():
        raise ValueError(f"Not a file: {p}")
    return p


def to_png(image: PILImage.Image, max_width: int) -> bytes:
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


def render_pdf(
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
            return render_pages_to_images(pdf, scale, start, end, max_width)
    except pdfium.PdfiumError as exc:
        raise ValueError(f"Failed to open PDF: {path}") from exc


def render_pages_to_images(
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
        image = Image(data=to_png(bitmap.to_pil(), max_width), format="png")
        images.append(image)
    return images
