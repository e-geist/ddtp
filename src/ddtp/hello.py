import logging
from typing import Any

from ddtp.marketdata.data import (
    book_event_from_dict,
)
from ddtp.marketdata.orderbook import Orderbook
from ddtp.serialization.config import KafkaTopics
from ddtp.serialization.consumer import consume_kafka_messages

logger = logging.getLogger("main")

SUBSCRIBED_INSTRUMENTS = {"PI_XBTUSD"}
books: dict[str, Orderbook] = {}


def consume_orderbook_event(instrument: str, event: dict[str, Any], timestamp: int):
    if instrument not in SUBSCRIBED_INSTRUMENTS:
        return

    event = book_event_from_dict(event)
    book = books.get(event.product_id)
    if not book:
        book = Orderbook()
        books[event.product_id] = book
    book.apply_event(event)
    logger.info(f"{event.product_id}: {book}")


def main():
    consume_kafka_messages(
        topic=KafkaTopics.MARKETDATA, callback=consume_orderbook_event
    )


if __name__ == "__main__":
    main()
