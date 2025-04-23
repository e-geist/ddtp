import datetime as dt
import uuid
from decimal import Decimal

from ddtp.marketdata.data import OrderbookSide
from ddtp.order_execution.data import OrderType, NewOrder, CancelOrder, ModifyOrder
from ddtp.serialization.config import KafkaTopics
from ddtp.serialization.producer import produce_message


def send_new_order_to_execution_engine(
    *,
    sender_identifier: str,
    product_id: str,
    side: OrderbookSide,
    order_type: OrderType,
    size: Decimal,
    limit_price: Decimal,
    stop_price: Decimal | None = None,
) -> str:
    client_order_id = str(uuid.uuid4())
    new_order = NewOrder(
        sender_id=sender_identifier,
        product_id=product_id,
        client_order_id=client_order_id,
        side=side,
        order_type=order_type,
        size=size,
        limit_price=limit_price,
        stop_price=stop_price,
    )
    produce_message(
        topic=KafkaTopics.ORDER_ENTRY, key=sender_identifier, message=new_order
    )
    return client_order_id


def send_cancel_order_to_execution_engine(
    *,
    sender_identifier: str,
    product_id: str,
    client_order_id: str,
    order_id: str | None = None,
):
    cancel_order = CancelOrder(
        sender_id=sender_identifier,
        product_id=product_id,
        client_order_id=client_order_id,
        order_id=order_id,
    )
    produce_message(
        topic=KafkaTopics.ORDER_ENTRY, key=sender_identifier, message=cancel_order
    )


def send_modify_order_to_execution_engine(
    *,
    sender_identifier: str,
    product_id: str,
    client_order_id: str,
    order_id: str | None = None,
    process_before: dt.datetime | None = None,
    size: Decimal | None = None,
    limit_price: Decimal | None = None,
    stop_price: Decimal | None = None,
):
    modify_order = ModifyOrder(
        sender_id=sender_identifier,
        product_id=product_id,
        client_order_id=client_order_id,
        order_id=order_id,
        process_before=process_before,
        size=size,
        limit_price=limit_price,
        stop_price=stop_price,
    )
    produce_message(
        topic=KafkaTopics.ORDER_ENTRY, key=sender_identifier, message=modify_order
    )
