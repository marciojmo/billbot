"""Message handling and response formatting service."""

import logging

from app.services.storage import get_user_boletos

logger = logging.getLogger(__name__)


def format_boletos_response(boletos: list[dict]) -> str:
    """Format the list of stored boletos as a response message.

    Args:
        boletos: List of boleto data dicts.

    Returns:
        A formatted string with all boletos.
    """
    if not boletos:
        return "Ainda não tenho nenhum boleto guardado. Me envia um boleto?"

    boleto_lines = "\n".join(
        [
            f"*{boleto['issuer']} - R$ {boleto['value']}:*\n{boleto['barcode']}\n"
            for boleto in boletos
        ]
    )

    return f"Aqui está a lista completa de boletos:\n\n{boleto_lines}"


async def get_user_boletos_response(telegram_id: int) -> str:
    """Get formatted response with user's boletos.

    Args:
        telegram_id: The Telegram user ID.

    Returns:
        Formatted string with all user's boletos.
    """
    boletos = await get_user_boletos(telegram_id)
    return format_boletos_response(boletos)
