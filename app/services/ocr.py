"""OCR service using OpenAI GPT-4o vision."""

import base64
import json
import logging

from openai import AsyncOpenAI

from app.schemas.boleto import BoletoData

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


class BoletoExtractor:
    """Extracts boleto data from images with an OpenAI vision model."""

    def __init__(self, client: AsyncOpenAI, model: str = "gpt-4o") -> None:
        """Create the extractor.

        Args:
            client: The OpenAI client to send requests with.
            model: The vision-capable model to use.
        """
        self._client = client
        self._model = model

    async def extract(self, image_bytes: bytes) -> BoletoData:
        """Extract boleto data from an image.

        Args:
            image_bytes: The image file content as bytes.

        Returns:
            BoletoData with extracted information and confidence level.
        """
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        response = await self._client.chat.completions.create(
            model=self._model,
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
        except json.JSONDecodeError as e:
            logger.error("Failed to parse OCR response: %s", e)
            return BoletoData(confidence=0.0, raw_text=content)

        return BoletoData(
            barcode=data.get("barcode"),
            due_date=data.get("due_date"),
            value=data.get("value"),
            issuer=data.get("issuer"),
            confidence=float(data.get("confidence", 0.0)),
            raw_text=data.get("raw_text"),
        )
