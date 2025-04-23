# Import WebSocket client library
import logging
import os
from time import sleep

from ddtp.api.kraken_derivatives.rest import KrakenDerivREST
from ddtp.api.kraken_derivatives.config import KrakenApiEnvVars
from ddtp.marketdata.data import (
    OrderBookSide,
)
from ddtp.order_entry.data import OrderType
from ddtp.serialization.config import KafkaTopics
from ddtp.serialization.consumer import consume_kafka_messages

logger = logging.getLogger("main")


def main():
    consume_kafka_messages(topic=KafkaTopics.MARKETDATA, callback=lambda x: ...)


if __name__ == "__main__":
    main()
