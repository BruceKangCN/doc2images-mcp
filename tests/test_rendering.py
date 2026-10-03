"""Tests for rendering document pages to images."""

from collections.abc import Callable
from pathlib import Path

import pytest
from fastmcp.utilities.types import Image
from PIL import Image as PILImage

from doc2images_mcp.main import pdf_to_images

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def test_sample_data_present(pdf_files: list[Path], data_dir: Path) -> None:
    assert pdf_files, f"expected sample PDFs in {data_dir}"


def test_render_pages(
    pdf: Path,
    decode: Callable[[Image], PILImage.Image],
    dump: Callable[[Path, int, Image], None],
) -> None:
    images = pdf_to_images(str(pdf), dpi=72, max_pages=2)

    assert 1 <= len(images) <= 2
    for index, image in enumerate(images, start=1):
        assert isinstance(image, Image)
        assert image.data is not None
        assert image.data[:8] == PNG_SIGNATURE
        decoded = decode(image)
        assert decoded.width > 0 and decoded.height > 0
        dump(pdf, index, image)


def test_dpi_controls_resolution(
    first_with_pages: Callable[[int], Path],
    decode: Callable[[Image], PILImage.Image],
) -> None:
    pdf = first_with_pages(1)

    small = decode(pdf_to_images(str(pdf), dpi=72, max_pages=1, max_width=100_000)[0])
    large = decode(pdf_to_images(str(pdf), dpi=144, max_pages=1, max_width=100_000)[0])

    assert large.width > small.width
    # add some tolerance which may be caused by rounding or alignment
    assert large.width == pytest.approx(144 / 72 * small.width, abs=8)


def test_max_width_downscales(
    first_with_pages: Callable[[int], Path],
    decode: Callable[[Image], PILImage.Image],
) -> None:
    pdf = first_with_pages(1)

    image = decode(pdf_to_images(str(pdf), dpi=200, max_pages=1, max_width=400)[0])

    assert image.width == 400
