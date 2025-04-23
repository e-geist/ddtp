import logging
import multiprocessing as mp
import os
from typing import Any

from ddtp.api.kraken_derivatives.config import KrakenApiEnvVars
from ddtp.api.kraken_derivatives.data import (
    FeedType,
    WS_MESSAGES_EVENT_FIELD,
    WS_MESSAGES_FEED_FIELD,
    Fills as KrakenFills,
    OpenOrdersSnapshot,
    OpenOrderDelta,
    OpenOrder,
)
from ddtp.api.kraken_derivatives.order_execution import process_order_action
from ddtp.api.kraken_derivatives.rest import KrakenDerivREST
from ddtp.api.kraken_derivatives.websocket import KrakenDerivWebSocket
from ddtp.marketdata.data import OrderbookSide
from ddtp.order_execution.data import (
    Fill,
    OrderUpdate,
    Order,
    OrderCancelUpdate,
    ORDER_ACTION_TYPE_FIELD_NAME,
    OrderActionType,
    NewOrder,
    ModifyOrder,
    CancelOrder,
)
from ddtp.order_execution.order_manager import OrderManager
from ddtp.serialization.config import KafkaTopics
from ddtp.serialization.consumer import consume_kafka_messages
from ddtp.serialization.producer import produce_message

logger = logging.getLogger("order_execution_engine")


clients = set[str]()

order_manager = OrderManager()
rest_api: KrakenDerivREST


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


def start_data_receival(feedback_queue: mp.Queue) -> None:
    # Connect to WebSocket API and subscribe to trade feed for XBT/USD and XRP/USD
    ws = _start_websocket(feedback_queue)

    while True:
        while ws.wst and ws.wst.is_alive():
            ws.wst.join()
        ws = _start_websocket(feedback_queue)


def get_on_order_action(order_manager_queue: mp.Queue):
    def on_order_action(key: str, message: dict[str, Any], timestamp: int):
        if key not in clients:
            clients.add(key)

        parsed_order_action: NewOrder | CancelOrder | ModifyOrder | None = None
        match message[ORDER_ACTION_TYPE_FIELD_NAME]:
            case OrderActionType.NEW_ORDER:
                parsed_order_action = NewOrder(**message)
            case OrderActionType.CANCEL_ORDER:
                parsed_order_action = CancelOrder(**message)
            case OrderActionType.MODIFY_ORDER:
                parsed_order_action = ModifyOrder(**message)

        process_order_action(parsed_order_action)
        order_manager_queue.put(parsed_order_action)

    return on_order_action


def _send_kafka_responses(queue: mp.Queue):
    while True:
        response: list[OrderUpdate] | list[Fill] | list[OrderCancelUpdate] = queue.get()
        if not response:
            continue
        # assume all messages in one response belong to one strategy
        key = response[0].sender_id
        produce_message(
            topic=KafkaTopics.ORDER_ENTRY_FEEDBACK, key=key, message=response
        )


def read_events(read_queue: mp.Queue, send_kafka: mp.Queue):
    while True:
        event = read_queue.get()
        order_manager.process_updates(event)
        match event:
            case list():
                send_kafka.put(event)


def main():
    logger.info("Starting execution engine")
    send_message_queue = mp.Queue()
    order_manager_queue = mp.Queue()

    receive_feedback_process = mp.Process(
        target=start_data_receival,
        args=(order_manager_queue,),
    )
    receive_feedback_process.start()

    send_kafka_process = mp.Process(
        target=_send_kafka_responses,
        args=(send_message_queue,),
    )
    send_kafka_process.start()

    receive_kafka_process = mp.Process(
        target=consume_kafka_messages,
        kwargs={
            "topic": KafkaTopics.ORDER_ENTRY,
            "callback": get_on_order_action(order_manager_queue),
        },
    )
    receive_kafka_process.start()

    read_events(order_manager_queue, send_message_queue)


if __name__ == "__main__":
    main()
