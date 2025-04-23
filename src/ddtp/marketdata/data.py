from decimal import Decimal
from enum import StrEnum
from typing import Optional, Any

from pydantic import BaseModel


class MessageType(StrEnum):
    BOOK_SNAPSHOT = "book_snapshot"
    BOOK = "book"
    TRADE = "trade"
    TRADE_SNAPSHOT = "trade_snapshot"


class OrderbookSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class TradeType(StrEnum):
    FILL = "fill"
    LIQUIDATION = "liquidation"
    TERMINATION = "termination"
    BLOCK = "block"


class BaseMessage(BaseModel):
    message_type: MessageType


class BookBase(BaseMessage):
    timestamp: int
    seq: int
    product_id: str


class OrderBookEntry(BaseModel):
    price: Decimal
    qty: Decimal


class BookSnapshot(BookBase):
    message_type: MessageType = MessageType.BOOK_SNAPSHOT
    tickSize: Optional[Decimal]
    bids: list[OrderBookEntry]
    asks: list[OrderBookEntry]


class BookDelta(BookBase):
    message_type: MessageType = MessageType.BOOK
    side: OrderbookSide
    price: Decimal
    qty: Decimal


class TradeBase(BaseMessage):
    product_id: str


class TradeData(BaseModel):
    uid: str
    side: OrderbookSide
    type: TradeType
    seq: int
    time: int
    qty: Decimal
    price: Decimal


class TradeSnapshot(TradeBase):
    message_type: MessageType = MessageType.TRADE_SNAPSHOT
    trades: list[TradeData]


class TradeDelta(TradeBase, TradeData):
    message_type: MessageType = MessageType.TRADE


MARKETDATA_MESSAGE_TYPE_NAME = "message_type"


def book_event_from_dict(
    event: dict[str, Any],
) -> BookSnapshot | BookDelta | TradeSnapshot | TradeDelta:
    match event[MARKETDATA_MESSAGE_TYPE_NAME]:
        case MessageType.BOOK:
            return BookDelta(**event)
        case MessageType.BOOK_SNAPSHOT:
            return BookSnapshot(**event)
        case MessageType.TRADE:
            return TradeDelta(**event)
        case MessageType.TRADE_SNAPSHOT:
            return TradeSnapshot(**event)

    raise TypeError(f"unknown event: {event}")
