import logging
import os
from typing import Any

from ddtp.api.kraken_derivatives.config import KrakenApiEnvVars
from ddtp.api.kraken_derivatives.rest import KrakenDerivREST
from ddtp.order_execution.data import (
    OrderActionType,
    NewOrder,
    CancelOrder,
    ModifyOrder,
    OrderState,
)
from ddtp.order_execution.order_manager import OrderManager
from ddtp.serialization.config import KafkaTopics
from ddtp.serialization.consumer import consume_kafka_messages

logger = logging.getLogger("order_execution_engine")


clients = set[str]()

order_manager = OrderManager()
rest_api: KrakenDerivREST


def process_new_action(new_order: NewOrder):
    rest_api.send_order(
        new_order.order_type,
        new_order.product_id,
        new_order.side,
        new_order.size,
        new_order.price,
        new_order.stop_price,
        new_order.client_order_id,
    )
    order_manager.add_pending_order(new_order.to_order())


def process_cancel_action(cancel_order: CancelOrder):
    if cancel_order.client_order_id:
        rest_api.cancel_order(cli_ord_id=cancel_order.client_order_id)
        order_manager.order_is_done(cancel_order.client_order_id, OrderState.CANCELLED)
    else:
        rest_api.cancel_order(order_id=cancel_order.order_id)
        order_manager.order_is_done(cancel_order.order_id, OrderState.CANCELLED)


def process_modify_action(modify_order: ModifyOrder):
    modify_query = dict[str, Any]()
    if modify_order.client_order_id:
        order_id = modify_order.client_order_id
        modify_query["orderId"] = order_id
    else:
        order_id = modify_order.order_id
        modify_query["cliOrdId"] = order_id

    if modify_order.size is not None:
        modify_query["size"] = modify_order.size

    if modify_order.limit_price is not None:
        modify_query["limitPrice"] = modify_order.limit_price

    if modify_order.stop_price is not None:
        modify_query["stopPrice"] = modify_order.stop_price

    rest_api.edit_order(modify_query)
    order_manager.update_active_order(
        order_id, size=modify_order.size, price=modify_order.price
    )


def on_order_action(key: str, message: dict[str, Any], timestamp: int):
    if key not in clients:
        clients.add(key)

    match message["ORDER_ACTION_TYPE_FIELD_NAME"]:
        case OrderActionType.NEW_ORDER:
            process_new_action(NewOrder(**message))
        case OrderActionType.CANCEL_ORDER:
            process_cancel_action(CancelOrder(**message))
        case OrderActionType.MODIFY_ORDER:
            process_modify_action(ModifyOrder(**message))


def main():
    global rest_api
    api_key = os.getenv(KrakenApiEnvVars.API_KEY)
    api_secret = os.getenv(KrakenApiEnvVars.API_SECRET)
    api_url = os.getenv(KrakenApiEnvVars.REST_BASE_URL)
    rest_api = KrakenDerivREST(api_url, api_key, api_secret)

    consume_kafka_messages(topic=KafkaTopics.ORDER_ENTRY, callback=on_order_action)


if __name__ == "__main__":
    main()
