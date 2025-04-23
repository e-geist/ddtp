import logging

from ddtp.marketdata.data import (
    BookSnapshot,
    BookDelta,
    TradeSnapshot,
    TradeDelta,
)
from ddtp.marketdata.orderbook import Orderbook
from ddtp.strategy.marketdata import subscribe_orderbook_data

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


def main():
    subscribe_orderbook_data(
        product_ids=SUBSCRIBED_INSTRUMENTS,
        on_orderbook_event=process_orderbook_event,
        on_trade=process_trade_event,
    )


if __name__ == "__main__":
    main()
