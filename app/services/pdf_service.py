"""PDF processing service."""

import logging

import fitz

logger = logging.getLogger(__name__)


def convert_pdf_to_images(pdf_bytes: bytes, dpi: int = 200) -> list[bytes]:
    """Convert PDF pages to images.

    Args:
        pdf_bytes: The PDF file content as bytes.
        dpi: The resolution for rendering pages (default 200).

    Returns:
        A list of PNG images as bytes, one per page.
    """
    images: list[bytes] = []

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=matrix)
        image_bytes = pix.tobytes("png")
        images.append(image_bytes)
        logger.info(f"Converted PDF page {page_num + 1}/{len(doc)} to image")

    doc.close()

    return images
