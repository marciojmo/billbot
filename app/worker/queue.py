"""In-process message queue for async processing."""

import asyncio
import contextlib
import logging
from collections.abc import Sequence

from app.schemas.queue import QueueMessage
from app.worker.consumers import Consumer

logger = logging.getLogger(__name__)


class MessageQueue:
    """An asyncio queue that runs every consumer, in order, on each message.

    A failing consumer is logged and skipped so later consumers still run.
    """

    def __init__(self, consumers: Sequence[Consumer]) -> None:
        """Create the queue.

        Args:
            consumers: Consumers to run on each message, in order.
        """
        self._consumers = list(consumers)
        self._queue: asyncio.Queue[QueueMessage] = asyncio.Queue()
        self._task: asyncio.Task[None] | None = None

    async def enqueue(self, message: QueueMessage) -> None:
        """Add a message to the queue.

        Args:
            message: The queue message to enqueue.
        """
        await self._queue.put(message)
        logger.info("Enqueued message %s (type: %s)", message.id, message.type)

    def start(self) -> None:
        """Start processing messages in a background task."""
        if self._task is None:
            self._task = asyncio.create_task(self._run(), name="message-queue")
            logger.info(
                "Queue processor started with consumers: %s",
                ", ".join(c.name for c in self._consumers),
            )

    async def stop(self) -> None:
        """Stop the background task. Pending messages are dropped."""
        if self._task is None:
            return
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None
        logger.info("Queue processor stopped")

    async def _run(self) -> None:
        """Process messages from the queue until cancelled."""
        while True:
            message = await self._queue.get()
            logger.info("Processing message %s", message.id)
            try:
                for consumer in self._consumers:
                    try:
                        await consumer(message)
                    except Exception:
                        logger.exception("Consumer %s failed", consumer.name)
            finally:
                self._queue.task_done()
