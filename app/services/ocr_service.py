"""OCR service using OpenAI GPT-4o vision."""

import base64
import json
import logging

from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.ocr import BoletoData

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an OCR specialist for Brazilian payment slips (boletos).
Analyze the image and extract the following information:

1. barcode: The complete barcode number (linha digitável - typically 47-48 digits)
2. due_date: The payment due date (data de vencimento) in DD/MM/YYYY format
3. value: The payment value (valor) in Brazilian Real format (e.g., "150,00" or "1.234,56")
4. issuer: The issuer/company name (cedente or beneficiário)
5. confidence: Your confidence level from 0.0 to 1.0 based on image quality and clarity

Always respond with a valid JSON object with these exact fields.
If you cannot read a field clearly, set it to null.
Be especially careful with the barcode - verify all digits are correct.
"""

USER_PROMPT = """Extract the boleto information from this image.
Return a JSON object with: barcode, due_date, value, issuer, confidence, raw_text.
The raw_text field should contain any additional relevant information you can see."""


async def extract_boleto_data(image_bytes: bytes) -> BoletoData:
    """Extract boleto data from an image using GPT-4o vision.

    Args:
        image_bytes: The image file content as bytes.

    Returns:
        BoletoData with extracted information and confidence level.

    Raises:
        ValueError: If the OpenAI API key is not configured.
    """
    if not settings.openai_api_key:
        logger.error("OPENAI_API_KEY environment variable is not set")
        raise ValueError("OpenAI API key is not configured")

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": USER_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high",
                        },
                    },
                ],
            },
        ],
        max_tokens=1000,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    if not content:
        logger.warning("Empty response from OpenAI")
        return BoletoData(confidence=0.0, raw_text="Empty response from OCR")

    try:
        data = json.loads(content)
        return BoletoData(
            barcode=data.get("barcode"),
            due_date=data.get("due_date"),
            value=data.get("value"),
            issuer=data.get("issuer"),
            confidence=float(data.get("confidence", 0.0)),
            raw_text=data.get("raw_text"),
        )
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OCR response: {e}")
        return BoletoData(confidence=0.0, raw_text=content)


def format_boleto_response(data: BoletoData) -> str:
    """Format the extracted boleto data as a user-friendly message.

    Args:
        data: The extracted boleto data.

    Returns:
        A formatted string with the boleto information.
    """
    confidence_pct = int(data.confidence * 100)

    lines = ["📄 *Dados do Boleto Extraídos*\n"]

    if data.barcode:
        lines.append(f"🔢 *Código de Barras:*\n`{data.barcode}`\n")
    else:
        lines.append("🔢 *Código de Barras:* Não identificado\n")

    if data.due_date:
        lines.append(f"📅 *Vencimento:* {data.due_date}")
    else:
        lines.append("📅 *Vencimento:* Não identificado")

    if data.value:
        lines.append(f"💰 *Valor:* R$ {data.value}")
    else:
        lines.append("💰 *Valor:* Não identificado")

    if data.issuer:
        lines.append(f"🏢 *Emissor:* {data.issuer}")
    else:
        lines.append("🏢 *Emissor:* Não identificado")

    lines.append(f"\n📊 *Confiança:* {confidence_pct}%")

    if data.raw_text and confidence_pct < 80:
        lines.append(f"\n📝 *Observações:* {data.raw_text}")

    return "\n".join(lines)
