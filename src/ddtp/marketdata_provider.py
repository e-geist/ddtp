import logging
import os

from ddtp.api.kraken_derivatives.websocket import KrakenDerivWebSocket
from ddtp.api.kraken_derivatives.config import KrakenApiEnvVars
from ddtp.serialization.config import KafkaTopics
from ddtp.serialization.producer import produce_message
from ddtp.marketdata.data import Orderbook, BookSubscribed, BookSnapshot, BookUpdate

books = dict[str, Orderbook]()

logger = logging.getLogger(__name__)

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


def _build_book(event: BookUpdate | BookSnapshot):
    book = books.get(event.product_id)
    if not book:
        book = Orderbook()
        books[event.product_id] = book
    produce_message(topic=KafkaTopics.MARKETDATA, key=event.product_id, message=event)

    book.apply_event(event)
    logger.info(f"{event.product_id}: {book}")

def main():
    api_key = os.getenv(KrakenApiEnvVars.API_KEY)
    api_secret = os.getenv(KrakenApiEnvVars.API_SECRET)

    # Connect to WebSocket API and subscribe to trade feed for XBT/USD and XRP/USD
    ws = KrakenDerivWebSocket(
        os.getenv(KrakenApiEnvVars.WS_BASE_URL),
        _on_message_handler,
        api_key,
        api_secret,
    )
    ws.subscribe_public("book", ["PI_XBTUSD", "PI_ETHUSD"])
    # ws.subscribe_private("open_orders")

    while True:
        pass

if __name__ == "__main__":
    main()
