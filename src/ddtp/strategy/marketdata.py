from typing import Callable, Any

from ddtp.marketdata.data import (
    BookSnapshot,
    BookDelta,
    TradeSnapshot,
    TradeDelta,
    book_event_from_dict,
)
from ddtp.serialization.config import KafkaTopics
from ddtp.serialization.consumer import consume_kafka_messages


def subscribe_orderbook_data(
    *,
    product_ids: set[str],
    on_trade: Callable[[TradeSnapshot | TradeDelta], None],
    on_orderbook_event: Callable[[BookSnapshot | BookDelta], None],
):
    def consume_orderbook_event(instrument: str, event: dict[str, Any], timestamp: int):
        if instrument not in product_ids:
            return

        event = book_event_from_dict(event)
        match event:
            case BookSnapshot() | BookDelta():
                on_orderbook_event(event)
            case TradeSnapshot() | TradeDelta():
                on_trade(event)

    consume_kafka_messages(
        topic=KafkaTopics.MARKETDATA, callback=consume_orderbook_event
    )
