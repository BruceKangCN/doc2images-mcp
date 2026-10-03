"""Shared pytest configuration and fixtures for the doc2images-mcp test suite."""

import io
import os
from collections.abc import Callable
from pathlib import Path

import pypdfium2 as pdfium
import pytest
from fastmcp.utilities.types import Image
from PIL import Image as PILImage

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Pin the base directory for relative paths to the project root *before* the
# package is imported, so tests are independent of the directory pytest is
# launched from.
os.environ["DOC2IMG_BASE_DIR"] = str(PROJECT_ROOT)

DATA_DIR = PROJECT_ROOT / "data"
TMP_DIR = PROJECT_ROOT / "tmp"
RENDER_DIR = TMP_DIR / "rendered"


def _sample_pdfs() -> list[Path]:
    return sorted(DATA_DIR.glob("*.pdf"))


def _page_count(path: Path) -> int:
    with pdfium.PdfDocument(path) as pdf:
        return len(pdf)


@pytest.fixture
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture
def data_dir() -> Path:
    return DATA_DIR


@pytest.fixture(scope="session")
def pdf_files() -> list[Path]:
    """All sample PDFs under ``data/``, sorted by name."""
    return _sample_pdfs()


@pytest.fixture
def first_with_pages() -> Callable[[int], Path]:
    """Return a picker for the first sample PDF with at least ``minimum`` pages."""

    def _pick(minimum: int) -> Path:
        for pdf in _sample_pdfs():
            if _page_count(pdf) >= minimum:
                return pdf
        pytest.skip(f"no sample PDF with at least {minimum} page(s) in {DATA_DIR}")

    return _pick


@pytest.fixture
def decode() -> Callable[[Image], PILImage.Image]:
    """Return a helper that decodes an MCP ``Image`` into a PIL image."""

    def _decode(image: Image) -> PILImage.Image:
        assert image.data is not None
        return PILImage.open(io.BytesIO(image.data))

    return _decode


@pytest.fixture
def dump() -> Callable[[Path, int, Image], None]:
    """Return a helper that writes a rendered page under ``tmp/rendered/``."""

    def _dump(pdf: Path, index: int, image: Image) -> None:
        assert image.data is not None
        out = RENDER_DIR / pdf.stem / f"page-{index:04}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(image.data)

    return _dump


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrize every test requesting ``pdf`` over all sample PDFs."""
    if "pdf" in metafunc.fixturenames:
        pdfs = _sample_pdfs()
        metafunc.parametrize("pdf", pdfs, ids=[p.stem for p in pdfs])
