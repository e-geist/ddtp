import logging
import multiprocessing as mp
from typing import Any, Callable

from ddtp.order_execution.data import (
    Fill,
    OrderUpdate,
    OrderCancelUpdate,
    ORDER_ACTION_TYPE_FIELD_NAME,
    OrderActionType,
    NewOrder,
    ModifyOrder,
    CancelOrder,
)
from ddtp.order_execution.execution_engine_adapter import (
    AvailableExecutionEngineAdapter,
)
from ddtp.order_execution.order_manager import OrderManager
from ddtp.serialization.config import KafkaTopics
from ddtp.serialization.consumer import consume_kafka_messages
from ddtp.serialization.producer import produce_message

logger = logging.getLogger("order_execution_engine")


clients = set[str]()

order_manager = OrderManager()


def get_on_order_action(
    order_manager_queue: mp.Queue,
    process_action: Callable[[NewOrder | CancelOrder | ModifyOrder], None],
):
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

        process_action(parsed_order_action)
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

    start_feedback_data_receival, send_order_action = (
        AvailableExecutionEngineAdapter.KRAKEN_DERIVATIVES.value
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
            "callback": get_on_order_action(order_manager_queue, send_order_action),
        },
    )
    receive_order_actions.start()

    read_events(order_manager_queue, send_message_queue)


if __name__ == "__main__":
    main()
