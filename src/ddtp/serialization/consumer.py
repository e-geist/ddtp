import logging
import os
import uuid
from typing import Callable, Any

import ormsgpack
from kafka import KafkaConsumer

from ddtp.serialization.config import KafkaClusterEnvVars, KafkaTopics

logger = logging.getLogger("kafka_consumer")


def consume_kafka_messages(
    *,
    topic: KafkaTopics,
    callback: Callable[[str, dict[str, Any], int], None],
    group_id: str | None,
    client_id: str | None = None,
):
    if client_id is None:
        client_id = str(uuid.uuid4())

    logging.info(
        f"subscribing to topic={topic.name}, with client_id={client_id} and group_id={group_id}"
    )
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=os.getenv(KafkaClusterEnvVars.BROKER),
        value_deserializer=ormsgpack.unpackb,
        key_deserializer=lambda key: key.decode("utf-8"),
        client_id=client_id,
        group_id=group_id,
    )

    for message in consumer:
        callback(message.key, message.value, message.timestamp)
