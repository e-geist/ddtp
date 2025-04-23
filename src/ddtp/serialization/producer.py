import decimal
import os

import ormsgpack

from kafka import KafkaProducer
from typing import Any, Iterable

from ddtp.serialization.config import KafkaTopics, KafkaClusterEnvVars

__producer = KafkaProducer(
    bootstrap_servers=os.getenv(KafkaClusterEnvVars.BROKER),
    value_serializer=lambda x: ormsgpack.packb(
        x, default=default, option=ormsgpack.OPT_SERIALIZE_PYDANTIC
    ),
    key_serializer=lambda k: k.encode("utf-8"),
)


def default(obj):
    if isinstance(obj, decimal.Decimal):
        return str(obj)
    raise TypeError


def produce_message(*, topic: KafkaTopics, key: Any, message: Any):
    __producer.send(topic, message, key=key)
    __producer.flush()


def produce_messages(*, topic: KafkaTopics, key: Any, messages: Iterable[Any]):
    for message in messages:
        __producer.send(topic, message, key=key)
    __producer.flush()
