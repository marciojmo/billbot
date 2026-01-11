"""OCR result schemas."""

from pydantic import BaseModel, Field


class BoletoData(BaseModel):
    """Extracted data from a boleto image.

    Attributes:
        barcode: The barcode number (código de barras).
        due_date: The payment due date.
        value: The payment value/cost.
        issuer: The issuer/company name.
        confidence: Confidence level of the extraction (0.0 to 1.0).
    """

    barcode: str | None = Field(
        None,
        description="The barcode number (linha digitável or código de barras)",
    )
    due_date: str | None = Field(
        None,
        description="The payment due date (data de vencimento)",
    )
    value: str | None = Field(
        None,
        description="The payment value/cost (valor)",
    )
    issuer: str | None = Field(
        None,
        description="The issuer/company name (cedente/beneficiário)",
    )
    confidence: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Confidence level of the extraction (0.0 to 1.0)",
    )
    raw_text: str | None = Field(
        None,
        description="Additional extracted text or notes",
    )
