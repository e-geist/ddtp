import logging
from decimal import Decimal

from ddtp.marketdata.data import (
    BookSnapshot,
    BookDelta,
    TradeSnapshot,
    TradeDelta,
    OrderbookSide,
)
from ddtp.marketdata.orderbook import Orderbook
from ddtp.order_execution.data import OrderType
from ddtp.strategy.marketdata import subscribe_orderbook_data
from ddtp.strategy.order_execution import (
    send_new_order_to_execution_engine,
    send_cancel_order_to_execution_engine,
)

logger = logging.getLogger("strategy")

SENDER_ID = "buy_small_spr_PI_XBTUSD_PI_ETHUSD"
SUBSCRIBED_INSTRUMENTS = {"PI_XBTUSD", "PI_ETHUSD"}
books = dict[str, Orderbook]()


def process_orderbook_event(event: BookSnapshot | BookDelta):
    book = books.get(event.product_id)
    if not book:
        book = Orderbook(event.product_id)
        books[event.product_id] = book
    book.apply_event(event)
    if book.is_initialized:
        logger.debug(f"Book: {event.product_id}: {book}")

        best_ask = book.get_best_ask()
        size = best_ask[1]
        if size == Decimal("0"):
            return

        client_order_id = send_new_order_to_execution_engine(
            sender_identifier=SENDER_ID,
            product_id=book.product_id,
            side=OrderbookSide.BUY,
            order_type=OrderType.LMT,
            size=Decimal("1"),
            limit_price=best_ask[0],
        )
        send_cancel_order_to_execution_engine(
            sender_identifier=SENDER_ID,
            product_id=book.product_id,
            client_order_id=client_order_id,
        )


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
