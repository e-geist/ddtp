import logging
from decimal import Decimal

from ddtp.order_execution.data import Order, OrderState

logger = logging.getLogger("order_manager")


class OrderManager:
    def __init__(self):
        self.active_orders = dict[str, Order]()
        self.pending_orders = dict[str, Order]()
        self.done_orders = dict[str, Order]()

    def add_pending_order(self, order: Order):
        if order.order_id in self.active_orders:
            raise ValueError(f"order with id {order.order_id} is already active")
        if order.order_id in self.pending_orders:
            raise ValueError(f"order with id {order.order_id} is already pending")
        if order.order_id in self.done_orders:
            raise ValueError(f"order with id {order.order_id} is already done")

        self.pending_orders[order.order_id] = order
        logger.info(f"added order {order.order_id}")

    def is_order_active(self, order_id: str) -> bool:
        return order_id in self.active_orders

    def is_order_pending(self, order_id: str) -> bool:
        return order_id in self.pending_orders

    def is_order_done(self, order_id: str) -> bool:
        return order_id in self.done_orders

    def order_is_done(
        self, order_id: str, state: OrderState, filled_size: Decimal | None = None
    ):
        order = self.active_orders.pop(order_id, None)
        if not order:
            raise ValueError(f"order with {order_id} is not active")

        order.state = state
        if filled_size is not None:
            order.filled_size = filled_size

        self.done_orders[order_id] = order

    def order_is_active(self, order_id: str):
        order = self.pending_orders.pop(order_id, None)
        if not order:
            raise ValueError(f"order with {order_id} is not pending")

        order.state = OrderState.ACTIVE
        self.active_orders[order_id] = order

    def update_active_order(
        self,
        order_id: str,
        state: OrderState | None = None,
        filled_size: Decimal | None = None,
        size: Decimal | None = None,
        price: Decimal | None = None,
    ) -> OrderState:
        order = self.active_orders.get(order_id)
        if not order:
            raise ValueError(
                f"order with {order_id} is not active and cannot be modified"
            )

        if state:
            order.state = state

        if filled_size:
            order.filled_size = filled_size

        if size:
            order.size = size

        if price:
            order.price = price

        if filled_size == size:
            order.state = OrderState.FILLED
            self.done_orders[order_id] = order
            self.active_orders.pop(order_id)

        return order.state
