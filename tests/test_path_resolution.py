"""Tests for resolving document paths."""

from collections.abc import Callable
from pathlib import Path

import pytest

from doc2images_mcp.main import pdf_to_images


def test_relative_path_resolves_against_base_dir(
    first_with_pages: Callable[[int], Path], project_root: Path
) -> None:
    pdf = first_with_pages(1)
    relative = pdf.relative_to(project_root).as_posix()

    assert len(pdf_to_images(relative, dpi=72, max_pages=1)) == 1


def test_rejects_missing_file(data_dir: Path) -> None:
    with pytest.raises(ValueError, match="Not a file"):
        pdf_to_images(str(data_dir / "does-not-exist.pdf"))
