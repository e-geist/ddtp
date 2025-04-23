"""Data type definitions for order entry."""

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel

from ddtp.marketdata.data import OrderBookSide

import datetime as dt


class OrderType(StrEnum):
    LMT = "lmt"
    POST = "post"
    IOC = "ioc"
    MKT = "mkt"
    STP = "stp"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"


class OrderBase(BaseModel):
    sender_identifier: str
    product_id: str


class NewOrder(BaseModel):
    side: OrderBookSide
    order_type: OrderType
    size: Decimal
    limit_price: Decimal
    stop_price: Decimal | None = (None,)
    client_order_id: str | None = None


class CancelOrder(BaseModel):
    order_id: str | None
    client_order_id: str | None = None


class ModifyOrder(BaseModel):
    order_id: str | None
    client_order_id: str | None = None
    process_before: dt.datetime | None = None
    size: Decimal | None = None
    limit_price: Decimal | None = None
