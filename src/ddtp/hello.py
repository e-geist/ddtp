# Import WebSocket client library
import logging
import os
from time import sleep

from ddtp.api.kraken_derivatives.rest import KrakenDerivREST
from ddtp.config.env_vars import KrakenApi
from ddtp.marketdata.data import (
    OrderBookSide,
)
from ddtp.order_entry.data import OrderType

logger = logging.getLogger("main")


def main():
    api_key = os.getenv(KrakenApi.API_KEY)
    api_secret = os.getenv(KrakenApi.API_SECRET)

    rest = KrakenDerivREST(
        os.getenv(KrakenApi.REST_BASE_URL),
        api_key,
        api_secret,
    )

    sleep(10)
    logger.info("Sending order.")
    order_response = rest.send_order(
        OrderType.LMT.value, "PF_ETHUSD", OrderBookSide.BUY, 1, 2200
    )
    logger.info(f"Order response: {order_response}")

    # Infinite loop waiting for WebSocket data
    while True:
        pass


if __name__ == "__main__":
    main()
