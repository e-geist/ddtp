"""Converts Kraken derivatives specific marketdata to internal marketdata representation."""

import logging
import os
from multiprocessing import Queue
from typing import Any, Callable

from ddtp.api.kraken_derivatives.websocket import KrakenDerivWebSocket
from ddtp.api.kraken_derivatives.config import KrakenApiEnvVars

from ddtp.marketdata.data import (
    BookSnapshot,
    BookDelta,
    TradeDelta,
    TradeSnapshot,
)
from ddtp.api.kraken_derivatives.data import (
    FeedType,
    WS_MESSAGES_FEED_FIELD,
    WS_MESSAGES_EVENT_FIELD,
)

logger = logging.getLogger(__name__)


def _get_marketdata_parser(queue: Queue) -> Callable[[dict[str, Any]], None]:
    def parse_marketdata_event(
        event: dict[str, Any],
    ):
        if WS_MESSAGES_EVENT_FIELD in event:
            return
        parsed_event = None
        feed = event.pop(WS_MESSAGES_FEED_FIELD)
        match feed:
            case FeedType.BOOK:
                parsed_event = BookDelta(**event)
            case FeedType.BOOK_SNAPSHOT:
                parsed_event = BookSnapshot(**event)
            case FeedType.TRADE:
                parsed_event = TradeDelta(**event)
            case FeedType.TRADE_SNAPSHOT:
                parsed_event = TradeSnapshot(**event)

        if not parsed_event:
            raise TypeError(f"missing handling of event: {event}")

        queue.put(parsed_event)

    return parse_marketdata_event


def _start_websocket(product_ids: list[str], queue: Queue) -> KrakenDerivWebSocket:
    api_key = os.getenv(KrakenApiEnvVars.API_KEY)
    api_secret = os.getenv(KrakenApiEnvVars.API_SECRET)
    logger.info("(re)starting websocket connection")
    ws = KrakenDerivWebSocket(
        os.getenv(KrakenApiEnvVars.WS_BASE_URL),
        _get_marketdata_parser(queue),
        api_key,
        api_secret,
    )
    ws.subscribe_public(FeedType.BOOK, product_ids)
    ws.subscribe_public(FeedType.TRADE, product_ids)
    return ws


def start_data_receival(product_ids: list[str], queue: Queue) -> None:
    # Connect to WebSocket API and subscribe to trade feed for XBT/USD and XRP/USD
    ws = _start_websocket(product_ids, queue)

    while True:
        while ws.wst and ws.wst.is_alive():
            ws.wst.join()
        ws = _start_websocket(product_ids, queue)
