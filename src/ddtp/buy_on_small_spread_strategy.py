import logging
import multiprocessing as mp
from decimal import Decimal

from ddtp.marketdata.data import (
    BookSnapshot,
    BookDelta,
    TradeSnapshot,
    TradeDelta,
    OrderbookSide,
)
from ddtp.marketdata.orderbook import Orderbook
from ddtp.order_execution.data import OrderType, Fill, OrderCancelUpdate, OrderUpdate, OrderState
from ddtp.order_execution.order_manager import OrderManager
from ddtp.strategy.marketdata import subscribe_orderbook_data
from ddtp.strategy.order_execution import (
    send_new_order_to_execution_engine,
    send_cancel_order_to_execution_engine,
    subscribe_order_feedback_data, send_modify_order_to_execution_engine,
)

logger = logging.getLogger("strategy")

TRADED_INSTRUMENT = "PI_XBTUSD"
SMALL_SPREAD_FACTOR = Decimal(0.001)

SENDER_ID = f"buy_small_spr_{TRADED_INSTRUMENT}"
book = Orderbook(TRADED_INSTRUMENT)
order_manager: OrderManager = OrderManager()
position: Decimal = Decimal("0")
latest_client_order_id: str | None = None

def update_positions(fills: list[Fill]):
    global position

    for fill in fills:
        position += fill.size if fill.side == OrderbookSide.BUY else -fill.size

def process_message(message: BookSnapshot | BookDelta | TradeSnapshot | TradeDelta | list[Fill] | list[OrderUpdate] | list[OrderCancelUpdate]):
    match message:
        case BookSnapshot() | BookDelta():
            process_orderbook_event(message)
        case TradeSnapshot() | TradeDelta():
            process_trade_event(message)
        case list():
            order_manager.process_updates(message)
            if message and isinstance(message[0], Fill):
                update_positions(message)

def process_orderbook_event(event: BookSnapshot | BookDelta):
    book.apply_event(event)
    if not book.is_initialized:
        return

    logger.debug(f"Book: {event.product_id}: {book}")

    best_ask = book.get_best_ask()
    best_bid = book.get_best_bid()

    best_ask_price = best_ask[0]
    best_bid_price = best_bid[0]

    small_spread = best_ask_price * SMALL_SPREAD_FACTOR

    if (best_ask_price - best_bid_price) > small_spread:
        return  # spread too big -> we don't want to place new orders

    if best_bid[1] == Decimal("0") or best_ask[1] == Decimal("0"):
        return # don't trade on an inactive book

    if position < Decimal("10"):
        side = OrderbookSide.BUY
        price = best_bid[0] + Decimal("100")
    else:
        side = OrderbookSide.SELL
        price = best_ask[0] - Decimal("100")

    global latest_client_order_id
    existing_order = order_manager.get_active_order(client_order_id=latest_client_order_id)
    if existing_order is None:
        sent_new_order = send_new_order_to_execution_engine(
            sender_id=SENDER_ID,
            product_id=book.product_id,
            side=side,
            order_type=OrderType.LMT,
            size=Decimal("1"),
            limit_price=price,
        )
        latest_client_order_id = sent_new_order.client_order_id
        order_manager.process_update(sent_new_order)
        return

    if existing_order.state != OrderState.ACTIVE:
        return # don't do anything if operations are pending

    # side cannot be modified -> cancel and place new order
    if existing_order.side != side:
        sent_cancel_order = send_cancel_order_to_execution_engine(
            sender_id=SENDER_ID,
            product_id=book.product_id,
            client_order_id=latest_client_order_id,
        )
        order_manager.process_update(sent_cancel_order)
        sent_new_order = send_new_order_to_execution_engine(
            sender_id=SENDER_ID,
            product_id=book.product_id,
            side=side,
            order_type=OrderType.LMT,
            size=Decimal("1"),
            limit_price=price,
        )
        latest_client_order_id = sent_new_order.client_order_id
        order_manager.process_update(sent_new_order)
        return

    if abs(existing_order.price - price) > SMALL_SPREAD_FACTOR * best_bid_price:
        sent_modify_order = send_modify_order_to_execution_engine(
            sender_id=SENDER_ID,
            client_order_id=latest_client_order_id,
            product_id=book.product_id,
            limit_price=price
        )
        order_manager.process_update(sent_modify_order)


def process_trade_event(event: TradeSnapshot | TradeDelta):
    logger.debug(f"Trade: {event.product_id}: {event}")


def main():
    logger.info("Starting buy on small spread strategy")
    data_queue = mp.Queue()

    receive_marketdata = mp.Process(
        target=subscribe_orderbook_data,
        kwargs={"product_ids": {TRADED_INSTRUMENT}, "queue": data_queue},
    )
    receive_marketdata.start()

    receive_order_feedback = mp.Process(
        target=subscribe_order_feedback_data,
        kwargs={"sender_id": SENDER_ID, "queue": data_queue},
    )
    receive_order_feedback.start()

    try:
        while True:
            message = data_queue.get()
            process_message(message)
    except KeyboardInterrupt:
        logger.info("Shutting down buy on small spread strategy")

    if receive_marketdata.is_alive():
        receive_marketdata.terminate()
        receive_marketdata.join()
        logger.info("Stopped receival of marketdata process")

    if receive_order_feedback.is_alive():
        receive_order_feedback.terminate()
        receive_order_feedback.join()
        logger.info("Stopped receival of order feedback process")

    logger.info("Shutdown complete buy on small spread strategy")


if __name__ == "__main__":
    main()
