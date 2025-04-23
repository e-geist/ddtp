from typing import List, Optional, Any
from pydantic import BaseModel
from decimal import Decimal
from enum import StrEnum


class FeedType(StrEnum):
    BOOK_SNAPSHOT = "book_snapshot"
    BOOK = "book"
    TRADE = "trade"
    TRADE_SNAPSHOT = "trade_snapshot"


class OrderBookSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class TradeType(StrEnum):
    FILL = "fill"
    LIQUIDATION = "liquidation"
    TERMINATION = "termination"
    BLOCK = "block"


class OrderBookEntry(BaseModel):
    price: Decimal
    qty: Decimal


class BaseMessage(BaseModel):
    feed: FeedType


class MarketdataSubscribed(BaseMessage):
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


class BookDelta(BookBase):
    side: OrderBookSide
    price: Decimal
    qty: Decimal


class TradeBase(BaseMessage):
    product_id: str


class TradeData(BaseModel):
    uid: str
    side: OrderBookSide
    type: TradeType
    seq: int
    time: int
    qty: Decimal
    price: Decimal


class TradeSnapshot(TradeBase):
    trades: list[TradeData]


class TradeDelta(TradeBase, TradeData):
    pass


def book_event_from_dict(event: dict[str, Any]) -> BookSnapshot | BookDelta | TradeSnapshot | TradeDelta:
    match event["feed"]:
        case FeedType.BOOK:
            return BookDelta(**event)
        case FeedType.BOOK_SNAPSHOT:
            return BookSnapshot(**event)
        case FeedType.TRADE:
            return TradeDelta(**event)
        case FeedType.TRADE_SNAPSHOT:
            return TradeSnapshot(**event)

    raise TypeError(f"unknown event: {event}")
