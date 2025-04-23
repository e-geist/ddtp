import datetime as dt
import multiprocessing as mp
import uuid
from decimal import Decimal
from typing import Any

from ddtp.marketdata.data import OrderbookSide
from ddtp.order_execution.data import (
    OrderType,
    NewOrder,
    CancelOrder,
    ModifyOrder,
    order_response_from_dict,
)
from ddtp.serialization.config import KafkaTopics
from ddtp.serialization.consumer import consume_kafka_messages
from ddtp.serialization.producer import produce_message


def send_new_order_to_execution_engine(
    *,
    sender_id: str,
    product_id: str,
    side: OrderbookSide,
    order_type: OrderType,
    size: Decimal,
    limit_price: Decimal,
    stop_price: Decimal | None = None,
) -> NewOrder:
    client_order_id = str(uuid.uuid4())
    new_order = NewOrder(
        sender_id=sender_id,
        product_id=product_id,
        client_order_id=client_order_id,
        side=side,
        order_type=order_type,
        size=size,
        limit_price=limit_price,
        stop_price=stop_price,
    )
    produce_message(
        topic=KafkaTopics.ORDER_ENTRY, key=sender_id, message=new_order
    )
    return new_order


def send_cancel_order_to_execution_engine(
    *,
    sender_id: str,
    product_id: str,
    client_order_id: str,
    order_id: str | None = None,
) -> CancelOrder:
    cancel_order = CancelOrder(
        sender_id=sender_id,
        product_id=product_id,
        client_order_id=client_order_id,
        order_id=order_id,
    )
    produce_message(
        topic=KafkaTopics.ORDER_ENTRY, key=sender_id, message=cancel_order
    )
    return cancel_order


def send_modify_order_to_execution_engine(
    *,
    sender_id: str,
    product_id: str,
    client_order_id: str,
    order_id: str | None = None,
    process_before: dt.datetime | None = None,
    size: Decimal | None = None,
    limit_price: Decimal | None = None,
    stop_price: Decimal | None = None,
) -> ModifyOrder:
    modify_order = ModifyOrder(
        sender_id=sender_id,
        product_id=product_id,
        client_order_id=client_order_id,
        order_id=order_id,
        process_before=process_before,
        size=size,
        limit_price=limit_price,
        stop_price=stop_price,
    )
    produce_message(
        topic=KafkaTopics.ORDER_ENTRY, key=sender_id, message=modify_order
    )

    return modify_order


def subscribe_order_feedback_data(
    *,
    sender_id: str,
    queue: mp.Queue,
):
    def consume_order_feedback_event(
        sender_id_message: str, event: dict[str, Any], timestamp: int
    ):
        if not sender_id == sender_id_message:
            # feedback is for another strategy
            return

        converted_event = order_response_from_dict(event)
        queue.put(converted_event)

    consume_kafka_messages(
        topic=KafkaTopics.ORDER_ENTRY_FEEDBACK, callback=consume_order_feedback_event
    )
