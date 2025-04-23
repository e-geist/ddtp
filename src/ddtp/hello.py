# Import WebSocket client library
import logging


from ddtp.api.kraken_derivatives.rest import KrakenDerivREST
from ddtp.api.kraken_derivatives.websocket import KrakenDerivWebSocket
from ddtp.marketdata.data import (
    BookSubscribed,
    BookSnapshot,
    BookUpdate,
    Orderbook,
    OrderBookSide,
)
from time import sleep

from ddtp.order_entry.data import OrderType

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


logger = logging.getLogger("main")

books = dict[str, Orderbook]()


def _on_message_handler(message):
    event = None
    if "event" in message:
        if "product_ids" in message:
            event = BookSubscribed(**message)
    elif "tickSize" in message:
        event = BookSnapshot(**message)
    elif "side" in message:
        event = BookUpdate(**message)

    if event:
        _build_book(event)
    else:
        logger.info(message)


def _build_book(book_data: BookUpdate | BookSnapshot):
    book = books.get(book_data.product_id)
    if not book:
        book = Orderbook()
        books[book_data.product_id] = book

    match book_data:
        case BookUpdate():
            book.apply_update(book_data)
        case BookSnapshot():
            book.apply_snapshot(book_data)
    logger.info(f"{book_data.product_id}: {book}")


def main():
    # Connect to WebSocket API and subscribe to trade feed for XBT/USD and XRP/USD
    ws = KrakenDerivWebSocket(
        "wss://demo-futures.kraken.com/ws/v1",
        _on_message_handler,
        "API_KEY",
        "API_SECRET",
    )
    # ws.subscribe_public("book", ["PI_XBTUSD", "PI_ETHUSD"])
    ws.subscribe_private("open_orders")

    rest = KrakenDerivREST(
        "https://demo-futures.kraken.com",
        "API_KEY",
        "API_SECRET",
    )

    sleep(10)
    logger.info("Sending order.")
    order_response = rest.send_order(
        OrderType.LMT.value, "PF_ETHUSD", OrderBookSide.BUY, 10, 2200
    )
    logger.info(f"Order response: {order_response}")

    # Infinite loop waiting for WebSocket data
    while True:
        pass


if __name__ == "__main__":
    main()
