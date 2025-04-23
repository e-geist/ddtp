from typing import List, Optional, Any
from pydantic import BaseModel
from decimal import Decimal
from enum import StrEnum


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


def book_event_from_dict(event: dict[str, Any]) -> BookSnapshot | BookUpdate:
    if "tickSize" in event:
        return BookSnapshot(**event)

    if "side" in event:
        return BookUpdate(**event)

    raise TypeError(f"unknown event: {event}")
