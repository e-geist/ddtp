"""Data type definitions for order entry."""

from enum import StrEnum


class OrderType(StrEnum):
    LMT = "lmt"
    POST = "post"
    IOC = "ioc"
    MKT = "mkt"
    STP = "stp"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"
