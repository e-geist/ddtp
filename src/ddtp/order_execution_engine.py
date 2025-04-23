import logging
import multiprocessing as mp
from typing import Any, Callable

from ddtp.order_execution.data import (
    Fill,
    OrderUpdate,
    OrderCancelUpdate,
    NewOrder,
    ModifyOrder,
    CancelOrder,
    order_action_from_dict,
)
from ddtp.order_execution.execution_engine_adapter import (
    AvailableExecutionEngineAdapter,
)
from ddtp.order_execution.order_manager import OrderManager
from ddtp.serialization.config import KafkaTopics
from ddtp.serialization.consumer import consume_kafka_messages
from ddtp.serialization.producer import produce_message

USED_ADAPTER = AvailableExecutionEngineAdapter.KRAKEN_DERIVATIVES
COMPONENT_NAME = "order_execution_engine"
IDENTIFIER = f"{COMPONENT_NAME}_{USED_ADAPTER.name}"
logger = logging.getLogger(IDENTIFIER)

order_manager = OrderManager()


def get_on_order_action(
    order_manager_queue: mp.Queue,
):
    def on_order_action(key: str, message: dict[str, Any], timestamp: int):
        parsed_order_action: NewOrder | CancelOrder | ModifyOrder = (
            order_action_from_dict(message)
        )
        order_manager_queue.put(parsed_order_action)
        logging.info(f"processing order action: {parsed_order_action}")

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


def main():
    logger.info("Starting execution engine")
    send_message_queue = mp.Queue()
    order_manager_queue = mp.Queue()

    start_feedback_data_receival, send_order_action = (
        USED_ADAPTER.value
    )

    receive_feedback_process = mp.Process(
        target=start_feedback_data_receival,
        args=(order_manager_queue,),
    )
    receive_feedback_process.start()

    send_kafka_process = mp.Process(
        target=_send_kafka_responses,
        args=(send_message_queue,),
    )
    send_kafka_process.start()

    receive_order_actions = mp.Process(
        target=consume_kafka_messages,
        kwargs={
            "topic": KafkaTopics.ORDER_ENTRY,
            "callback": get_on_order_action(order_manager_queue),
            "group_id": IDENTIFIER,
            "client_id": IDENTIFIER,
        },
    )
    receive_order_actions.start()

    while send_kafka_process.is_alive() and receive_order_actions.is_alive() and receive_feedback_process.is_alive():
        event = order_manager_queue.get()
        order_manager.process_updates(event)
        match event:
            case NewOrder() | CancelOrder() | ModifyOrder():
                send_order_action(event)
            case list():
                send_message_queue.put(event)


if __name__ == "__main__":
    main()
