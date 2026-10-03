"""Tests for selecting which pages are rendered."""

from collections.abc import Callable
from pathlib import Path

from doc2images_mcp.main import pdf_to_images


def test_max_pages_caps_output(first_with_pages: Callable[[int], Path]) -> None:
    pdf = first_with_pages(3)

    assert len(pdf_to_images(str(pdf), dpi=72, max_pages=1)) == 1
    assert len(pdf_to_images(str(pdf), dpi=72, max_pages=2)) == 2


def test_first_and_last_page(first_with_pages: Callable[[int], Path]) -> None:
    pdf = first_with_pages(2)

    images = pdf_to_images(str(pdf), dpi=72, first_page=2, last_page=2, max_pages=10)

    assert len(images) == 1
