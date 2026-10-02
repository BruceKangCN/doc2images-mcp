"""Integration tests for the pdf_to_images MCP tool.

Sample PDFs live in ``data/``. Rendered pages are written under
``tmp/rendered/`` for manual inspection; that directory is git-ignored.
"""

import importlib
import io
import sys
from pathlib import Path

import pypdfium2 as pdfium
import pytest
from fastmcp.utilities.types import Image
from PIL import Image as PILImage

from doc2images_mcp.main import (
    HARD_MAX_PAGES,
    MAX_DPI,
    MIN_DPI,
    pdf_to_images,
)

main_module = importlib.import_module("doc2images_mcp.main")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RENDER_DIR = PROJECT_ROOT / "tmp" / "rendered"
SCRATCH_DIR = PROJECT_ROOT / "tmp" / "scratch"

PDF_FILES = sorted(DATA_DIR.glob("*.pdf"))

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _decode(image: Image) -> PILImage.Image:
    assert image.data is not None
    return PILImage.open(io.BytesIO(image.data))


def _page_count(path: Path) -> int:
    with pdfium.PdfDocument(path) as pdf:
        return len(pdf)


def _first_with_pages(minimum: int) -> Path:
    for pdf in PDF_FILES:
        if _page_count(pdf) >= minimum:
            return pdf
    pytest.skip(f"no sample PDF with at least {minimum} page(s) in {DATA_DIR}")


def _dump(pdf: Path, index: int, image: Image) -> None:
    assert image.data is not None
    out = RENDER_DIR / pdf.stem / f"page-{index:04}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(image.data)


def test_sample_data_present() -> None:
    assert PDF_FILES, f"expected sample PDFs in {DATA_DIR}"


@pytest.mark.parametrize("pdf", PDF_FILES, ids=[p.stem for p in PDF_FILES])
def test_render_pages(pdf: Path) -> None:
    images = pdf_to_images(str(pdf), dpi=72, max_pages=2)

    assert 1 <= len(images) <= 2
    for index, image in enumerate(images, start=1):
        assert isinstance(image, Image)
        assert image.data is not None
        assert image.data[:8] == PNG_SIGNATURE
        decoded = _decode(image)
        assert decoded.width > 0 and decoded.height > 0
        _dump(pdf, index, image)


def test_max_pages_caps_output() -> None:
    pdf = _first_with_pages(3)

    assert len(pdf_to_images(str(pdf), dpi=72, max_pages=1)) == 1
    assert len(pdf_to_images(str(pdf), dpi=72, max_pages=2)) == 2


def test_dpi_controls_resolution() -> None:
    pdf = _first_with_pages(1)

    small = _decode(pdf_to_images(str(pdf), dpi=72, max_pages=1, max_width=100_000)[0])
    large = _decode(pdf_to_images(str(pdf), dpi=144, max_pages=1, max_width=100_000)[0])

    assert large.width > small.width
    # add some tolerance which may be caused by rounding or alignment
    assert large.width == pytest.approx(144 / 72 * small.width, abs=8)


def test_max_width_downscales() -> None:
    pdf = _first_with_pages(1)

    image = _decode(pdf_to_images(str(pdf), dpi=200, max_pages=1, max_width=400)[0])

    assert image.width == 400


def test_first_and_last_page() -> None:
    pdf = _first_with_pages(2)

    images = pdf_to_images(str(pdf), dpi=72, first_page=2, last_page=2, max_pages=10)

    assert len(images) == 1


def test_relative_path_resolves_against_base_dir() -> None:
    pdf = _first_with_pages(1)
    relative = pdf.relative_to(PROJECT_ROOT).as_posix()

    assert len(pdf_to_images(relative, dpi=72, max_pages=1)) == 1


def test_rejects_missing_file() -> None:
    with pytest.raises(ValueError, match="Not a file"):
        pdf_to_images(str(DATA_DIR / "does-not-exist.pdf"))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"dpi": MIN_DPI - 1},
        {"dpi": MAX_DPI + 1},
        {"first_page": 0},
        {"last_page": 1, "first_page": 2},
        {"max_pages": 0},
        {"max_pages": HARD_MAX_PAGES + 1},
        {"max_width": 0},
    ],
)
def test_rejects_invalid_parameters(kwargs: dict) -> None:
    pdf = _first_with_pages(1)

    with pytest.raises(ValueError):
        pdf_to_images(str(pdf), **kwargs)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(pytest.main([__file__, "-v"]))
