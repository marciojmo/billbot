"""User-facing bot messages (Portuguese) and formatters."""

from app.schemas.boleto import StoredBoleto

START_TEMPLATE = (
    "Olá, {name}! Eu sou o Bill, seu assistente de pagamentos! "
    "Me envie seus boletos e eu te retornarei somente os códigos de barras dos mesmos."
)
PROCESSING = "🔄 Processando mensagem... Já aviso quando estiver pronto! 😉"
INVALID_MESSAGE = "Não consegui processar essa mensagem. Pode tentar novamente?"
DOWNLOAD_FAILED = "Não consegui baixar o arquivo, você poderia enviá-lo novamente?"
PDF_UNREADABLE = "Não consegui abrir esse PDF. Será que o arquivo está correto?"
PDF_EMPTY = "Não encontrei nenhuma página nesse PDF. Pode verificar o arquivo?"
NO_BOLETOS = "Ainda não tenho nenhum boleto guardado. Me envia um boleto?"
DEFAULT_NAME = "usuário"


def format_start(name: str | None) -> str:
    """Build the greeting for the /start command.

    Args:
        name: The user's first name, if known.

    Returns:
        The personalized greeting.
    """
    return START_TEMPLATE.format(name=name or DEFAULT_NAME)


def format_boleto_list(boletos: list[StoredBoleto]) -> str:
    """Format a user's stored boletos as a Markdown message.

    Args:
        boletos: The boletos to list.

    Returns:
        The formatted message.
    """
    if not boletos:
        return NO_BOLETOS

    boleto_lines = "\n".join(
        f"*{boleto.issuer} - R$ {boleto.value}:*\n{boleto.barcode}\n"
        for boleto in boletos
    )
    return f"Aqui está a lista completa de boletos:\n\n{boleto_lines}"
