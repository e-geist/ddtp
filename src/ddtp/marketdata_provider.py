import logging

from ddtp.marketdata.marketdata_adapter import AvailableMarketdataAdapter

logger = logging.getLogger(__name__)


def main():
    logger.info("Starting Marketdata Provider")
    AvailableMarketdataAdapter.KRAKEN_DERIVATIVES(["PI_XBTUSD", "PI_ETHUSD"])

    while True:
        pass


if __name__ == "__main__":
    main()
