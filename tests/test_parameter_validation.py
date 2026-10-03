"""Tests for rejecting invalid ``pdf_to_images`` parameters."""

from collections.abc import Callable
from pathlib import Path

import pytest

from doc2images_mcp.main import (
    HARD_MAX_PAGES,
    MAX_DPI,
    MIN_DPI,
    pdf_to_images,
)


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
def test_rejects_invalid_parameters(
    first_with_pages: Callable[[int], Path], kwargs: dict
) -> None:
    pdf = first_with_pages(1)

    with pytest.raises(ValueError):
        pdf_to_images(str(pdf), **kwargs)
