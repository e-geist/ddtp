import os
from typing import Callable

import ormsgpack
from kafka import KafkaConsumer

from ddtp.serialization.config import KafkaClusterEnvVars, KafkaTopics


def consume_kafka_messages(*, topic: KafkaTopics, callback: Callable):
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=os.getenv(KafkaClusterEnvVars.BROKER),
        value_deserializer=ormsgpack.unpackb,
        key_deserializer=lambda key: str(key),
    )

    for message in consumer:
        print(message.key, message.value, message.timestamp)
