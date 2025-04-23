# Import WebSocket client library
import logging

from ddtp.marketdata.kraken_derivatives.data import (
    BookSubscribed,
    BookSnapshot,
    BookUpdate, Orderbook,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

from ddtp.marketdata.kraken_derivatives.websocket import KrakenDerivWebSocket

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
        # logger.info(f"Received message: {event}")
        _build_book(event)

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
        "wss://demo-futures.kraken.com/ws/v1", _on_message_handler
    )
    ws.subscribe_public("book", ["PI_XBTUSD", "PI_ETHUSD"])
    # Infinite loop waiting for WebSocket data
    while True:
        pass


if __name__ == "__main__":
    main()
