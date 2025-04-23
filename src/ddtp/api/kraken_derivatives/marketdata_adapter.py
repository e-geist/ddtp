"""Converts Kraken derivatives specific marketdata to internal marketdata representation."""

import os
from typing import Any

from ddtp.api.kraken_derivatives.websocket import KrakenDerivWebSocket
from ddtp.api.kraken_derivatives.config import KrakenApiEnvVars

from ddtp.marketdata.data import (
    BookSnapshot,
    BookDelta,
    FeedType, TradeDelta, TradeSnapshot,
)
from ddtp.serialization.config import KafkaTopics
from ddtp.serialization.producer import produce_message


def parse_marketdata_event(
    event: dict[str, Any],
):
    if "event" in event:
        return
    parsed_event = None
    match event["feed"]:
        case FeedType.BOOK:
            parsed_event = BookDelta(**event)
        case FeedType.BOOK_SNAPSHOT:
            parsed_event = BookSnapshot(**event)
        case FeedType.TRADE:
            parsed_event = TradeDelta(**event)
        case FeedType.TRADE_SNAPSHOT:
            parsed_event = TradeSnapshot(**event)

    if not parsed_event:
        raise TypeError(f"Missing handling of event: {event}")

    produce_message(
        topic=KafkaTopics.MARKETDATA,
        key=parsed_event.product_id,
        message=parsed_event,
    )


def start_data_receival(product_ids: list[str]) -> None:
    api_key = os.getenv(KrakenApiEnvVars.API_KEY)
    api_secret = os.getenv(KrakenApiEnvVars.API_SECRET)

    # Connect to WebSocket API and subscribe to trade feed for XBT/USD and XRP/USD
    ws = KrakenDerivWebSocket(
        os.getenv(KrakenApiEnvVars.WS_BASE_URL),
        parse_marketdata_event,
        api_key,
        api_secret,
    )
    ws.subscribe_public(FeedType.BOOK, product_ids)
    ws.subscribe_public(FeedType.TRADE, product_ids)
