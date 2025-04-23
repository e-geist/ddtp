"""Data type definitions for order entry."""

import datetime as dt
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, computed_field

from ddtp.marketdata.data import OrderbookSide


class OrderType(StrEnum):
    LMT = "lmt"
    POST = "post"
    IOC = "ioc"
    MKT = "mkt"
    STP = "stp"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"


ORDER_ACTION_TYPE_FIELD_NAME = "action_type"


class OrderActionType(StrEnum):
    NEW_ORDER = "NEW_ORDER"
    CANCEL_ORDER = "CANCEL_ORDER"
    MODIFY_ORDER = "MODIFY_ORDER"


class OrderState(StrEnum):
    ACTIVE_PENDING = "active_pending"
    ACTIVE = "active"
    CANCEL_PENDING = "cancel_pending"
    CANCELLED = "cancelled"
    FILLED = "filled"
    MODIFY_PENDING = "modify_pending"


class Order(BaseModel):
    order_id: str
    product_id: str
    state: OrderState
    side: OrderbookSide
    size: Decimal
    price: Decimal
    type: OrderType
    filled_size: Decimal
    stop_price: Decimal | None = None

    @computed_field
    @property
    def open_size(self) -> Decimal:
        return self.size - self.filled_size


class OrderBase(BaseModel):
    action_type: OrderActionType
    sender_identifier: str
    product_id: str
    client_order_id: str | None = None


class NewOrder(OrderBase):
    action_type: OrderActionType = OrderActionType.NEW_ORDER
    side: OrderbookSide
    order_type: OrderType
    size: Decimal
    limit_price: Decimal
    stop_price: Decimal | None = None

    def to_order(self) -> Order:
        return Order(
            order_id=self.client_order_id,
            product_id=self.product_id,
            state=OrderState.ACTIVE_PENDING,
            side=self.side,
            type=self.order_type,
            size=self.size,
            price=self.limit_price,
            filled_size=Decimal("0"),
            stop_price=self.stop_price,
        )


class CancelOrder(OrderBase):
    action_type: OrderActionType = OrderActionType.CANCEL_ORDER
    order_id: str | None


class ModifyOrder(OrderBase):
    action_type: OrderActionType = OrderActionType.MODIFY_ORDER
    order_id: str | None
    process_before: dt.datetime | None = None
    size: Decimal | None = None
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
