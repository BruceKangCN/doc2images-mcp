# doc2images-mcp

An MCP server that renders documents to images and returns them directly as
**multimodal content** for the model.

- Deterministic "document -> image" conversion only;
- Does **not** convert documents to Markdown and does **not** do LLM-based
  document understanding / OCR;
- PDF rendering is handled by **pypdfium2** (PDFium), a self-contained Python
  wheel with no external binaries. PDFium ships its own encoding data,
  including the CJK CMaps, so Chinese/Japanese/Korean text renders correctly.

> This version supports PDF only. The DOCX / PPTX branch is reserved in the
> code and will be enabled once LibreOffice is wired in.

## Requirements

| Dependency | Notes |
|---|---|
| Python | `>= 3.14` (see `.python-version`) |
| [uv](https://docs.astral.sh/uv/) | Dependency management and run entry point |

No system packages are required: pypdfium2 bundles the PDFium binaries.

## Install

```shell
uv tool install doc2images-mcp
```

## Wiring it into OpenCode

Add the following to the `mcp.servers` section of `opencode.jsonc`:

```jsonc
"doc2images": {
  "type": "local",
  "command": [
    "uvx",
    "doc2images-mcp",
  ],
},
```

To cap how much image data reaches the context, you can also tighten
OpenCode's image settings:

```jsonc
"media": {
  "image": {
    "auto_resize": true,
    "max_width": 2000,
    "max_height": 2000,
    "max_base64_bytes": 5242880,
  },
},
```

## Tool: `pdf_to_images`

Renders PDF pages and returns a list of images (one per page).

| Parameter | Default | Description |
|---|---|---|
| `file_path` | — | Document path. Relative paths resolve against `DOC2IMG_BASE_DIR` |
| `dpi` | `150` | Rasterization resolution, `72`–`300`. Higher is sharper and larger |
| `first_page` | `1` | First page to render (1-based) |
| `last_page` | `0` | Last page to render; `0` means "up to `max_pages`" |
| `max_pages` | `10` | Hard cap on the number of pages (1–50) to protect the context |
| `max_width` | `3000` | Maximum output width; wider pages are scaled down proportionally |

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DOC2IMG_BASE_DIR` | Current working directory | Base directory used to resolve relative paths |

## Testing

Sample PDFs live in `data/`; the tests render them through the tool:

```powershell
uv run pytest -v
```

Rendered intermediate images are written to `tmp/`, which is ignored via its
own `.gitignore`.

## Roadmap

- **Office support**: after installing LibreOffice, add
  `soffice --headless --convert-to pdf` for `.docx/.pptx/.ppt` in the dispatch
  function, then reuse the same rendering logic.
- **Embedded image extraction**: extract only the images embedded in a
  document instead of whole pages.
- **Alternative backend**: PyMuPDF (`fitz`) is a drop-in alternative if its
  richer text/embedded-image APIs are ever needed; the tool interface stays
  the same.
