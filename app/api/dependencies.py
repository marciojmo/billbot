"""Shared API dependencies."""

from typing import Annotated

from fastapi import Depends, Request
from telegram import Bot

from app.bot.gateway import TelegramGateway
from app.container import Container
from app.worker.queue import MessageQueue


def get_container(request: Request) -> Container:
    """Get the application container built during startup.

    Args:
        request: The incoming request.

    Returns:
        The application container.
    """
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(get_container)]


def get_bot(container: ContainerDep) -> Bot:
    """Get the Telegram bot.

    Args:
        container: The application container.

    Returns:
        The Telegram bot.
    """
    return container.bot


def get_gateway(bot: Annotated[Bot, Depends(get_bot)]) -> TelegramGateway:
    """Get a Telegram gateway for the bot.

    Args:
        bot: The Telegram bot.

    Returns:
        The Telegram gateway.
    """
    return TelegramGateway(bot)


def get_queue(container: ContainerDep) -> MessageQueue:
    """Get the message queue.

    Args:
        container: The application container.

    Returns:
        The message queue.
    """
    return container.queue


BotDep = Annotated[Bot, Depends(get_bot)]
GatewayDep = Annotated[TelegramGateway, Depends(get_gateway)]
QueueDep = Annotated[MessageQueue, Depends(get_queue)]
