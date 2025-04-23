import decimal
import os

import ormsgpack

from kafka import KafkaProducer
from typing import Any, Iterable

from ddtp.serialization.config import KafkaTopics, KafkaClusterEnvVars


__producer: KafkaProducer | None = None


def _get_kafka_producer() -> KafkaProducer:
    global __producer
    if not __producer:
        __producer = KafkaProducer(
            bootstrap_servers=os.getenv(KafkaClusterEnvVars.BROKER),
            value_serializer=lambda x: ormsgpack.packb(
                x, default=default, option=ormsgpack.OPT_SERIALIZE_PYDANTIC
            ),
            key_serializer=lambda k: k.encode("utf-8"),
        )
    return __producer


def default(obj):
    if isinstance(obj, decimal.Decimal):
        return str(obj)
    raise TypeError


def produce_message(*, topic: KafkaTopics, key: Any, message: Any):
    producer = _get_kafka_producer()
    producer.send(topic, message, key=key)
    producer.flush()


def produce_messages(*, topic: KafkaTopics, key: Any, messages: Iterable[Any]):
    producer = _get_kafka_producer()
    for message in messages:
        producer.send(topic, message, key=key)
    producer.flush()
