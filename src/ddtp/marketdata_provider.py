import logging
import multiprocessing as mp
from multiprocessing import Process

from ddtp.marketdata.data import TradeSnapshot, TradeDelta, BookSnapshot, BookDelta
from ddtp.marketdata.marketdata_adapter import AvailableMarketdataAdapter
from ddtp.marketdata.orderbook import Orderbook
from ddtp.serialization.config import KafkaTopics
from ddtp.serialization.producer import produce_message

logger = logging.getLogger("marketdata_provider")

books = dict[str, Orderbook]()
sent_snapshots = dict[str, int]()


def main():
    logger.info("Starting Marketdata Provider")
    queue = mp.Queue()

    p = Process(
        target=AvailableMarketdataAdapter.KRAKEN_DERIVATIVES,
        args=(["PI_XBTUSD", "PI_ETHUSD"], queue),
    )
    p.start()

    try:
        while p.is_alive():
            event: TradeSnapshot | TradeDelta | BookSnapshot | BookDelta = queue.get()
            produce_message(
                topic=KafkaTopics.MARKETDATA,
                key=event.product_id,
                message=event,
            )

            match event:
                case BookDelta():
                    book = books[event.product_id]
                    book.apply_event(event)
                    difference_to_last_sent_snapshot = (
                        event.seq - sent_snapshots[event.product_id]
                    )
                    # sending all x messages a snapshot in case clients
                    # disconnect, so they don't need to read from the beginning
                    if difference_to_last_sent_snapshot > 400:
                        produce_message(
                            topic=KafkaTopics.MARKETDATA,
                            key=event.product_id,
                            message=book.to_snapshot(),
                        )
                        sent_snapshots[event.product_id] = event.seq
                case BookSnapshot():
                    book = Orderbook(event.product_id)
                    books[event.product_id] = book
                    book.apply_event(event)
                    sent_snapshots[event.product_id] = event.seq
    except KeyboardInterrupt:
        logger.info("Stopping Marketdata Provider")
    if p.is_alive():
        p.terminate()
        p.join()


if __name__ == "__main__":
    main()
