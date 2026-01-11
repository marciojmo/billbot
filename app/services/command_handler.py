"""Command processing service."""

START_MESSAGE_TEMPLATE = (
    "Olá, {name}! Eu sou o Bill, seu assistente de pagamentos! "
    "Me envie seus boletos e eu te retornarei somente os códigos de barras dos mesmos."
)


def get_start_message(name: str) -> str:
    """Get the greeting message for the /start command.

    Args:
        name: The user's first name.

    Returns:
        The personalized greeting message in Portuguese.
    """
    return START_MESSAGE_TEMPLATE.format(name=name)
