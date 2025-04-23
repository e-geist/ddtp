import os
from typing import Callable, Any

import ormsgpack
from kafka import KafkaConsumer

from ddtp.serialization.config import KafkaClusterEnvVars, KafkaTopics


def consume_kafka_messages(
    *, topic: KafkaTopics, callback: Callable[[str, dict[str, Any], int], None]
):
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=os.getenv(KafkaClusterEnvVars.BROKER),
        value_deserializer=ormsgpack.unpackb,
        key_deserializer=lambda key: key.decode("utf-8"),
        auto_offset_reset='earliest'
    )

    for message in consumer:
        callback(message.key, message.value, message.timestamp)
