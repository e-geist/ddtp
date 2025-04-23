import logging
from collections import defaultdict
from decimal import Decimal

from ddtp.marketdata.data import BookSnapshot, BookDelta, OrderBookSide, OrderBookEntry


class Orderbook:
    def __init__(self, product_id: str):
        self.is_initialized = False
        self.bids = defaultdict(Decimal)
        self.asks = defaultdict(Decimal)
        self.seq = 0
        self.held_back_updates = list[BookDelta]()
        self.product_id = product_id
        self._logger = logging.getLogger(f"orderbook {self.product_id}")
        self.last_update = 0
        self.tick_size = Decimal("0")

    def apply_event(self, event: BookSnapshot | BookDelta):
        match event:
            case BookDelta():
                self._apply_delta(event)
            case BookSnapshot():
                self._apply_snapshot(event)

    def _apply_snapshot(self, snapshot: BookSnapshot):
        if snapshot.seq <= self.seq:
            self._logger.info(
                f"skipping snapshot with seq={snapshot.seq}, as ob is already at {self.seq}"
            )
            return

        self.bids.clear()
        self.asks.clear()

        self.seq = snapshot.seq
        self.bids = {bid.price: bid.qty for bid in snapshot.bids}
        self.asks = {ask.price: ask.qty for ask in snapshot.asks}
        self.is_initialized = True
        self.tick_size = snapshot.tickSize
        self.last_update = snapshot.timestamp

        self._logger.info(f"applied snapshot with seq={snapshot.seq}")
        self._logger.info(f"applying {len(self.held_back_updates)} held back updates")
        while self.held_back_updates:
            delta = self.held_back_updates.pop(0)
            self._apply_delta(delta)

        self._logger.info("applying held back updates done!")

    def _apply_delta(self, delta: BookDelta):
        if not self.is_initialized:
            self.held_back_updates.append(delta)
            return

        if delta.seq <= self.seq:
            self._logger.warning(f"dropping book delta with seq={delta.seq}")
            return  # TODO Ignore out-of-order updates

        if delta.seq != self.seq + 1:
            raise ValueError(f"expected seq {self.seq + 1}, but got {delta.seq}")

        self.seq = delta.seq
        self.last_update = delta.timestamp

        side_to_modify = self.bids if delta.side == OrderBookSide.BUY else self.asks
        if delta.qty == 0 and delta.price in side_to_modify:
            del side_to_modify[delta.price]
        else:
            side_to_modify[delta.price] = delta.qty

    def get_best_bid(self) -> (Decimal, Decimal):
        if not self.bids:
            return Decimal(0), Decimal(0)
        best_bid_price = max(self.bids.keys())
        return best_bid_price, self.bids[best_bid_price]

    def get_best_ask(self) -> (Decimal, Decimal):
        if not self.asks:
            return Decimal(0), Decimal(0)
        best_ask_price = min(self.asks.keys())
        return best_ask_price, self.asks[best_ask_price]

    def __str__(self):
        bids_sorted = sorted(self.bids.items(), key=lambda x: x[0], reverse=True)
        asks_sorted = sorted(self.asks.items(), key=lambda x: x[0])
        return f"Bids: {bids_sorted}\nAsks: {asks_sorted}"

    def to_snapshot(self) -> BookSnapshot:
        bids = [
            OrderBookEntry(price=price, qty=qty) for price, qty in self.bids.items()
        ]
        ask = [OrderBookEntry(price=price, qty=qty) for price, qty in self.asks.items()]
        return BookSnapshot(
            product_id=self.product_id,
            tickSize=self.tick_size,
            bids=bids,
            asks=ask,
            seq=self.seq,
            timestamp=self.last_update,
        )
