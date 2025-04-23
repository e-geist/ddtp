import decimal
import os

import ormsgpack

from kafka import KafkaProducer
from typing import Any, Iterable

from ddtp.serialization.config import KafkaTopics, KafkaClusterEnvVars

__producer = KafkaProducer(
    bootstrap_servers=os.getenv(KafkaClusterEnvVars.BROKER),
    value_serializer=lambda x: ormsgpack.packb(x, default=default, option=ormsgpack.OPT_SERIALIZE_PYDANTIC),
)

def default(obj):
     if isinstance(obj, decimal.Decimal):
        return str(obj)
     raise TypeError

def produce_message(message: Any, topic: KafkaTopics):
    __producer.send(topic, message)
    __producer.flush()


def produce_messages(messages: Iterable[Any], topic: KafkaTopics):
    for message in messages:
        __producer.send(topic, message)
    __producer.flush()