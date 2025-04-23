from collections import defaultdict
from typing import List, Optional
from pydantic import BaseModel
from decimal import Decimal
from enum import Enum, StrEnum


class FeedType(StrEnum):
    BOOK_SNAPSHOT = "book_snapshot"
    BOOK = "book"

class OrderBookSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderBookEntry(BaseModel):
    price: Decimal
    qty: Decimal


class BaseMessage(BaseModel):
    feed: FeedType


class BookSubscribed(BaseMessage):
    event: str | None = None
    product_ids: list[str]


class BookBase(BaseMessage):
    timestamp: int
    seq: int
    product_id: str


class BookSnapshot(BookBase):
    tickSize: Optional[Decimal]
    bids: List[OrderBookEntry]
    asks: List[OrderBookEntry]


class BookUpdate(BookBase):
    side: OrderBookSide
    price: Decimal
    qty: Decimal

class Orderbook:
    def __init__(self):
        self.bids = defaultdict(Decimal)
        self.asks = defaultdict(Decimal)
        self.seq = 0

    def apply_snapshot(self, snapshot: BookSnapshot):
        self.bids.clear()
        self.asks.clear()
        self.seq = snapshot.seq
        for bid in snapshot.bids:
            self.bids[bid.price] = bid.qty
        for ask in snapshot.asks:
            self.asks[ask.price] = ask.qty

    def apply_update(self, update: BookUpdate):
        if update.seq <= self.seq:
            return  # TODO Ignore out-of-order updates
        self.seq = update.seq
        side_to_modify = self.bids if update.side == OrderBookSide.BUY else self.asks
        if update.qty == 0 and update.price in side_to_modify:
            del side_to_modify[update.price]
        else:
            side_to_modify[update.price] = update.qty

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