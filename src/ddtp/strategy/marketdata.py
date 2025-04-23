from typing import Any
import multiprocessing as mp
from ddtp.marketdata.data import (
    book_event_from_dict,
)
from ddtp.serialization.config import KafkaTopics
from ddtp.serialization.consumer import consume_kafka_messages


def subscribe_orderbook_data(
    *,
    product_ids: set[str],
    queue: mp.Queue,
):
    def consume_orderbook_event(instrument: str, event: dict[str, Any], timestamp: int):
        if instrument not in product_ids:
            return

        converted_event = book_event_from_dict(event)
        queue.put(converted_event)

    consume_kafka_messages(
        topic=KafkaTopics.MARKETDATA, callback=consume_orderbook_event
    )
