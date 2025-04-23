import logging
import multiprocessing as mp
import os
from typing import Any

from ddtp.api.kraken_derivatives.config import KrakenApiEnvVars
from ddtp.api.kraken_derivatives.data import OpenOrdersSnapshot, OpenOrder, OpenOrderDelta, Fills as KrakenFills, \
    WS_MESSAGES_EVENT_FIELD, WS_MESSAGES_FEED_FIELD, FeedType
from ddtp.api.kraken_derivatives.rest import KrakenDerivREST
from ddtp.api.kraken_derivatives.websocket import KrakenDerivWebSocket
from ddtp.marketdata.data import OrderbookSide
from ddtp.order_execution.data import NewOrder, CancelOrder, ModifyOrder, OrderUpdate, OrderCancelUpdate, Fill

api_key = os.getenv(KrakenApiEnvVars.API_KEY)
api_secret = os.getenv(KrakenApiEnvVars.API_SECRET)
api_url = os.getenv(KrakenApiEnvVars.REST_BASE_URL)
rest_api = KrakenDerivREST(api_url, api_key, api_secret)

logger = logging.getLogger("kraken_deriv_execution_engine_adapter")

def process_new_action(new_order: NewOrder):
    rest_api.send_order(
        new_order.order_type,
        new_order.product_id,
        new_order.side,
        new_order.size,
        new_order.limit_price,
        new_order.stop_price,
        new_order.client_order_id,
    )


def process_cancel_action(cancel_order: CancelOrder):
    rest_api.cancel_order(
        cli_ord_id=cancel_order.client_order_id, order_id=cancel_order.order_id
    )


def process_modify_action(modify_order: ModifyOrder):
    modify_query = dict[str, Any]()

    modify_query["cliOrdId"] = modify_order.client_order_id
    modify_query["orderId"] = modify_order.order_id

    if modify_order.size is not None:
        modify_query["size"] = modify_order.size

    if modify_order.limit_price is not None:
        modify_query["limitPrice"] = modify_order.limit_price

    if modify_order.stop_price is not None:
        modify_query["stopPrice"] = modify_order.stop_price

    rest_api.edit_order(modify_query)


def process_order_action(order_action: NewOrder | ModifyOrder | CancelOrder):
    match order_action:
        case NewOrder():
            process_new_action(order_action)
        case ModifyOrder():
            process_modify_action(order_action)
        case CancelOrder():
            process_cancel_action(order_action)


def parse_open_orders_snapshot(event: OpenOrdersSnapshot) -> list[OrderUpdate]:
    open_orders = list[OrderUpdate]()
    event_order: OpenOrder
    for event_order in event.orders:
        open_orders.append(
            OrderUpdate(
                product_id=event_order.instrument,
                time=event_order.time,
                last_update_time=event_order.last_update_time,
                client_order_id=event_order.cli_ord_id,
                order_id=event_order.order_id,
                order_type=event_order.type.to_internal(),
                side=event_order.direction.to_internal(),
                size=event_order.qty,
                filled=event_order.filled,
                price=event_order.limit_price,
                stop_price=event_order.stop_price,
                is_active=event_order.filled != event_order.qty,
                state_change_reason=None,
            )
        )

    return open_orders


def parse_open_order(event: OpenOrderDelta) -> OrderUpdate | OrderCancelUpdate:
    if event.order:
        event_order: OpenOrder = event.order
        order_update = OrderUpdate(
            product_id=event_order.instrument,
            time=event_order.time,
            last_update_time=event_order.last_update_time,
            client_order_id=event_order.cli_ord_id if event_order.cli_ord_id else None,
            order_id=event_order.order_id,
            order_type=event_order.type.to_internal(),
            side=event_order.direction.to_internal(),
            size=event_order.qty,
            filled=event_order.filled,
            price=event_order.limit_price,
            stop_price=event_order.stop_price,
            is_active=not event.is_cancel,
            state_change_reason=event.reason.to_internal(),
        )
    else:
        order_update = OrderCancelUpdate(
            order_id=event.order_id,
            client_order_id=None,
            is_active=not event.is_cancel,
            state_change_reason=event.reason.to_internal(),
        )

    return order_update


def parse_fills(event: KrakenFills) -> list[Fill]:
    fills = list[Fill]()
    for fill in event.fills:
        fills.append(
            Fill(
                product_id=fill.instrument,
                client_order_id=fill.cli_ord_id,
                order_id=fill.order_id,
                fill_id=fill.fill_id,
                time=fill.time,
                side=OrderbookSide.BUY if fill.buy else OrderbookSide.SELL,
                price=fill.price,
                size=fill.qty,
                remaining_size=fill.remaining_order_qty,
            ),
        )
    return fills


def get_message_parser(queue: mp.Queue):
    def parse_order_responses(
        event: dict[str, Any],
    ):
        if WS_MESSAGES_EVENT_FIELD in event:
            return
        parsed_events: (
            list[OrderUpdate] | list[Fill] | list[OrderCancelUpdate] | None
        ) = None
        logger.info(f"{event[WS_MESSAGES_FEED_FIELD]} event: {event}")
        match event[WS_MESSAGES_FEED_FIELD]:
            case FeedType.OPEN_ORDERS_SNAPSHOT:
                open_orders_snapshot = OpenOrdersSnapshot(**event)
                parsed_events = parse_open_orders_snapshot(open_orders_snapshot)
            case FeedType.OPEN_ORDERS:
                parsed_events = [parse_open_order(OpenOrderDelta(**event))]
            case FeedType.FILLS_SNAPSHOT | FeedType.FILLS:
                fills = KrakenFills(**event)
                parsed_events = parse_fills(fills)

        if parsed_events is None:
            raise TypeError(f"missing handling of event: {event}")
        queue.put(parsed_events)

    return parse_order_responses


def _start_websocket(queue: mp.Queue) -> KrakenDerivWebSocket:
    api_key = os.getenv(KrakenApiEnvVars.API_KEY)
    api_secret = os.getenv(KrakenApiEnvVars.API_SECRET)
    logger.info("(re)starting websocket connection")
    ws = KrakenDerivWebSocket(
        os.getenv(KrakenApiEnvVars.WS_BASE_URL),
        get_message_parser(queue),
        api_key,
        api_secret,
    )
    ws.subscribe_private(FeedType.OPEN_ORDERS)
    ws.subscribe_private(FeedType.FILLS)
    return ws


def start_feedback_data_receival(feedback_queue: mp.Queue) -> None:
    # Connect to WebSocket API and subscribe to trade feed for XBT/USD and XRP/USD
    ws = _start_websocket(feedback_queue)

    while True:
        while ws.wst and ws.wst.is_alive():
            ws.wst.join()
        ws = _start_websocket(feedback_queue)
