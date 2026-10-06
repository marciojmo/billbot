"""PDF rendering."""

import logging

import fitz

logger = logging.getLogger(__name__)


def render_pdf_pages(pdf_bytes: bytes, dpi: int = 200) -> list[bytes]:
    """Render each PDF page to a PNG image.

    This is CPU-bound and blocking; call it via ``asyncio.to_thread`` from
    async code.

    Args:
        pdf_bytes: The PDF file content as bytes.
        dpi: The resolution for rendering pages (default 200).

    Returns:
        A list of PNG images as bytes, one per page.
    """
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    images: list[bytes] = []

    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page_num, page in enumerate(doc, start=1):
            images.append(page.get_pixmap(matrix=matrix).tobytes("png"))
            logger.info("Converted PDF page %d/%d to image", page_num, len(doc))

    return images
