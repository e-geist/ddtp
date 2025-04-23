import os
from typing import Any

from ddtp.api.kraken_derivatives.config import KrakenApiEnvVars
from ddtp.api.kraken_derivatives.rest import KrakenDerivREST
from ddtp.order_execution.data import NewOrder, CancelOrder, ModifyOrder

api_key = os.getenv(KrakenApiEnvVars.API_KEY)
api_secret = os.getenv(KrakenApiEnvVars.API_SECRET)
api_url = os.getenv(KrakenApiEnvVars.REST_BASE_URL)
rest_api = KrakenDerivREST(api_url, api_key, api_secret)


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
