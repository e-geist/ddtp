"""Data type definitions for order entry."""

import datetime as dt
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, computed_field

from ddtp.marketdata.data import OrderbookSide

UNKNOWN_SENDER_ID = "UNKNOWN"


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
    sender_id: str = UNKNOWN_SENDER_ID
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
    sender_id: str = UNKNOWN_SENDER_ID
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
            sender_id=self.sender_id,
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
    order_id: str | None = None


class ModifyOrder(OrderBase):
    action_type: OrderActionType = OrderActionType.MODIFY_ORDER
    order_id: str | None
    process_before: dt.datetime | None = None
    size: Decimal | None = None
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None


class OrderActionResponseType(StrEnum):
    FILL = "fill"
    ORDER_UPDATE = "order_state"
    ORDER_CANCEL = "order_cancel"


class OrderResponse(BaseModel):
    response_type: OrderActionType
    sender_id: str = UNKNOWN_SENDER_ID
    product_id: str
    client_order_id: str | None = None
    order_id: str
    side: OrderbookSide
    size: Decimal
    price: Decimal


class OrderStateChangeReason(StrEnum):
    PARTIAL_FILL = "partial_fill"
    FILL = "fill"
    NEW_ORDER = "new_order"
    ORDER_FOR_MODIFY_NOT_FOUND = "order_for_modiy_not_found"
    OWN_CANCEL = "cancelled_by_user"
    CONTRACT_EXPIRED = "contract_expired"
    INSUFFICIENT_MARGIN = "insufficient_margin"
    MARKET_INACTIVE = "market_inactive"
    CANCELLED_BY_ADMIN = "cancelled_by_admin"
    IOC_ORDER_FAIL = "ioc_order_failed"
    POST_ORDER_FAIL = "post_order_failed"
    WOULD_EXECUTE_SELF = "would_execute_self"
    WOULD_NOT_REDUCE_POSITION = "would_not_reduce_position"
    MISC = "misc"


class OrderUpdate(OrderResponse):
    response_type: OrderActionType = OrderActionResponseType.ORDER_UPDATE
    order_type: OrderType
    time: int
    last_update_time: int
    filled: Decimal | None = None
    stop_price: Decimal | None = None
    is_active: bool = True
    state_change_reason: OrderStateChangeReason | None = None


class OrderCancelUpdate(BaseModel):
    response_type: OrderActionType = OrderActionResponseType.ORDER_CANCEL
    sender_id: str = UNKNOWN_SENDER_ID
    order_id: str
    client_order_id: str | None = None
    state_change_reason: OrderStateChangeReason
    is_active: bool = False


class Fill(OrderResponse):
    response_type: OrderActionType = OrderActionResponseType.FILL
    time: int
    fill_id: str
    remaining_size: Decimal
