from decimal import Decimal
from enum import StrEnum, Enum

from pydantic import BaseModel

from ddtp.marketdata.data import OrderbookSide
from ddtp.order_execution.data import OrderType, OrderStateChangeReason

WS_MESSAGES_FEED_FIELD = "feed"
WS_MESSAGES_EVENT_FIELD = "event"


class FeedType(StrEnum):
    BOOK_SNAPSHOT = "book_snapshot"
    BOOK = "book"
    TRADE = "trade"
    TRADE_SNAPSHOT = "trade_snapshot"
    FILLS_SNAPSHOT = "fills_snapshot"
    FILLS = "fills"
    OPEN_ORDERS_SNAPSHOT = "open_orders_snapshot"
    OPEN_ORDERS = "open_orders"


class FillType(StrEnum):
    MAKER = "maker"
    TAKER = "taker"
    LIQUIDATION = "liquidation"
    ASSIGNEE = "assignee"
    ASSIGNOR = "assignor"
    UNWIND_BANKRUPT = "unwindBankrupt"
    UNWIND_COUNTERPARTY = "unwindCounterparty"
    TAKER_AFTER_EDIT = "takerAfterEdit"


class ResponseBase(BaseModel):
    feed: FeedType
    account: str | None = None


class Fill(BaseModel):
    instrument: str
    time: int
    price: Decimal
    seq: int
    buy: bool
    qty: Decimal
    remaining_order_qty: Decimal
    order_id: str
    cli_ord_id: str | None = None
    fill_id: str
    fill_type: FillType
    fee_paid: Decimal


class Fills(ResponseBase):
    feed: FeedType = FeedType.FILLS
    fills: list[Fill]


class OpenOrderType(StrEnum):
    LIMIT = "limit"
    TAKE_PROFIT = "take_profit"
    STOP = "stop"

    def to_internal(self) -> OrderType:
        return {
            OpenOrderType.LIMIT: OrderType.LMT,
            OpenOrderType.TAKE_PROFIT: OrderType.TAKE_PROFIT,
            OpenOrderType.STOP: OrderType.STP,
        }[self]


class OpenOrderTriggerSignal(StrEnum):
    LAST = "last"
    MARK = "mark"
    SPOT = "spot"


class OpenOrderTrailingStopUnit(StrEnum):
    PERCENT = "percent"
    QUOTE_CURRENCY = "quote_currency"


class OpenOrderReason(StrEnum):
    NEW_PLACED_ORDER_BY_USER = "new_placed_order_by_user"
    LIQUIDATION = "liquidation"
    STOP_ORDER_TRIGGERED = "stop_order_triggered"
    LIMIT_ORDER_FROM_STOP = "limit_order_from_stop"
    PARTIAL_FILL = "partial_fill"
    FULL_FILL = "full_fill"
    CANCELLED_BY_USER = "cancelled_by_user"
    CONTRACT_EXPIRED = "contract_expired"
    NOT_ENOUGH_MARGIN = "not_enough_margin"
    MARKET_INACTIVE = "market_inactive"
    CANCELLED_BY_ADMIN = "cancelled_by_admin"
    DEAD_MAN_SWITCH = "dead_man_switch"
    IOC_ORDER_FAILED_BECAUSE_IT_WOULD_NOT_BE_EXECUTED = (
        "ioc_order_failed_because_it_would_not_be_executed"
    )
    POST_ORDER_FAILED_BECAUSE_IT_WOULD_FILLED = (
        "post_order_failed_because_it_would_filled"
    )
    WOULD_EXECUTE_SELF = "would_execute_self"
    WOULD_NOT_REDUCE_POSITION = "would_not_reduce_position"
    ORDER_FOR_EDIT_NOT_FOUND = "order_for_edit_not_found"

    def to_internal(self) -> OrderStateChangeReason:
        mapping = {
            OpenOrderReason.NEW_PLACED_ORDER_BY_USER: OrderStateChangeReason.NEW_ORDER,
            OpenOrderReason.LIQUIDATION: OrderStateChangeReason.MISC,
            OpenOrderReason.STOP_ORDER_TRIGGERED: OrderStateChangeReason.MISC,
            OpenOrderReason.LIMIT_ORDER_FROM_STOP: OrderStateChangeReason.MISC,
            OpenOrderReason.PARTIAL_FILL: OrderStateChangeReason.PARTIAL_FILL,
            OpenOrderReason.FULL_FILL: OrderStateChangeReason.FILL,
            OpenOrderReason.CANCELLED_BY_USER: OrderStateChangeReason.OWN_CANCEL,
            OpenOrderReason.CONTRACT_EXPIRED: OrderStateChangeReason.CONTRACT_EXPIRED,
            OpenOrderReason.NOT_ENOUGH_MARGIN: OrderStateChangeReason.INSUFFICIENT_MARGIN,
            OpenOrderReason.MARKET_INACTIVE: OrderStateChangeReason.MARKET_INACTIVE,
            OpenOrderReason.CANCELLED_BY_ADMIN: OrderStateChangeReason.CANCELLED_BY_ADMIN,
            OpenOrderReason.DEAD_MAN_SWITCH: OrderStateChangeReason.MISC,
            OpenOrderReason.IOC_ORDER_FAILED_BECAUSE_IT_WOULD_NOT_BE_EXECUTED: OrderStateChangeReason.IOC_ORDER_FAIL,
            OpenOrderReason.POST_ORDER_FAILED_BECAUSE_IT_WOULD_FILLED: OrderStateChangeReason.POST_ORDER_FAIL,
            OpenOrderReason.WOULD_EXECUTE_SELF: OrderStateChangeReason.WOULD_EXECUTE_SELF,
            OpenOrderReason.WOULD_NOT_REDUCE_POSITION: OrderStateChangeReason.WOULD_NOT_REDUCE_POSITION,
            OpenOrderReason.ORDER_FOR_EDIT_NOT_FOUND: OrderStateChangeReason.ORDER_FOR_MODIFY_NOT_FOUND,
        }

        return mapping.get(self, OrderStateChangeReason.MISC)


class OpenOrderTrailingStopOptions(BaseModel):
    max_deviation: Decimal
    unit: OpenOrderTrailingStopUnit


class OpenOrderDirection(Enum):
    BUY = 0
    SELL = 1

    def to_internal(self):
        return {
            OpenOrderDirection.BUY: OrderbookSide.BUY,
            OpenOrderDirection.SELL: OrderbookSide.SELL,
        }[self]


class OpenOrder(BaseModel):
    instrument: str
    time: int
    last_update_time: int
    qty: Decimal
    filled: Decimal
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    type: OpenOrderType
    order_id: str
    cli_ord_id: str | None = None
    direction: OpenOrderDirection
    reduce_only: bool
    trigger_signal: OpenOrderTriggerSignal | None = None
    trailing_stop_options: list[OpenOrderTrailingStopOptions] | None = None


class OpenOrderDelta(ResponseBase):
    feed: FeedType = FeedType.OPEN_ORDERS
    order: OpenOrder | None = None
    order_id: str | None = None
    is_cancel: bool
    reason: OpenOrderReason


class OpenOrdersSnapshot(ResponseBase):
    feed: FeedType = FeedType.OPEN_ORDERS_SNAPSHOT
    orders: list[OpenOrder]
