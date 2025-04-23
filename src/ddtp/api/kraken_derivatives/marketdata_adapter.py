"""Converts Kraken derivatives specific marketdata to internal marketdata representation."""

import os
from typing import Any

from ddtp.api.kraken_derivatives.websocket import KrakenDerivWebSocket
from ddtp.api.kraken_derivatives.config import KrakenApiEnvVars

from ddtp.marketdata.data import BookSnapshot, BookUpdate, BookSubscribed, BookBase
from ddtp.serialization.config import KafkaTopics
from ddtp.serialization.producer import produce_message


def parse_marketdata_event(
    event: dict[str, Any],
) -> BookSnapshot | BookUpdate | BookSubscribed | None:
    parsed_event = None
    if "tickSize" in event:
        parsed_event = BookSnapshot(**event)

    if "side" in event:
        parsed_event = BookUpdate(**event)

    if "event" and "product_ids" in event:
        parsed_event = BookSubscribed(**event)

    if isinstance(parsed_event, BookBase):
        produce_message(
            topic=KafkaTopics.MARKETDATA,
            key=parsed_event.product_id,
            message=parsed_event,
        )


def start_data_receival() -> None:
    api_key = os.getenv(KrakenApiEnvVars.API_KEY)
    api_secret = os.getenv(KrakenApiEnvVars.API_SECRET)

    # Connect to WebSocket API and subscribe to trade feed for XBT/USD and XRP/USD
    ws = KrakenDerivWebSocket(
        os.getenv(KrakenApiEnvVars.WS_BASE_URL),
        parse_marketdata_event,
        api_key,
        api_secret,
    )
    ws.subscribe_public("book", ["PI_XBTUSD", "PI_ETHUSD"])
    # ws.subscribe_private("open_orders")
