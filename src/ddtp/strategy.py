import logging
from typing import Any

from ddtp.marketdata.data import (
    book_event_from_dict,
    BookSnapshot,
    BookDelta,
    TradeSnapshot,
    TradeDelta,
)
from ddtp.marketdata.orderbook import Orderbook
from ddtp.serialization.config import KafkaTopics
from ddtp.serialization.consumer import consume_kafka_messages

logger = logging.getLogger("strategy")

SUBSCRIBED_INSTRUMENTS = {"PI_XBTUSD", "PI_ETHUSD"}
books = dict[str, Orderbook]()


def process_orderbook_event(event: BookSnapshot | BookDelta):
    book = books.get(event.product_id)
    if not book:
        book = Orderbook(event.product_id)
        books[event.product_id] = book
    book.apply_event(event)
    logger.debug(f"Book: {event.product_id}: {book}")


def process_trade_event(event: TradeSnapshot | TradeDelta):
    logger.debug(f"Trade: {event.product_id}: {event}")


def consume_orderbook_event(instrument: str, event: dict[str, Any], timestamp: int):
    if instrument not in SUBSCRIBED_INSTRUMENTS:
        return

    event = book_event_from_dict(event)
    match event:
        case BookSnapshot() | BookDelta():
            process_orderbook_event(event)
        case TradeSnapshot() | TradeDelta():
            process_trade_event(event)


def main():
    consume_kafka_messages(
        topic=KafkaTopics.MARKETDATA, callback=consume_orderbook_event
    )


if __name__ == "__main__":
    main()
