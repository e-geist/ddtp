import logging
from decimal import Decimal

from ddtp.order_execution.data import (
    Order,
    OrderState,
    NewOrder,
    CancelOrder,
    ModifyOrder,
    OrderCancelUpdate,
    OrderUpdate, UNKNOWN_SENDER_ID,
)

logger = logging.getLogger("order_manager")


class OrderManager:
    def __init__(self):
        self.active_orders = dict[str, Order]()
        self.done_orders = dict[str, Order]()

        self.order_id_to_client_order_id = dict[str, str]()
        self.client_order_id_to_sender_id = dict[str, str]()

    def set_sender_id_if_needed(self, update: NewOrder | CancelOrder | ModifyOrder | OrderCancelUpdate | OrderUpdate):
        if update.sender_id != UNKNOWN_SENDER_ID:
            return

        order_id_to_use = self.order_id_to_client_order_id.get(update.order_id)
        match update:
            case NewOrder() | ModifyOrder() | OrderUpdate() | CancelOrder() if update.client_order_id:
                order_id_to_use = update.client_order_id

        sender_id = self.client_order_id_to_sender_id.get(order_id_to_use, UNKNOWN_SENDER_ID)
        update.sender_id = sender_id

    def process_update(
        self,
        update: NewOrder | CancelOrder | ModifyOrder | OrderCancelUpdate | OrderUpdate,
    ):
        self.set_sender_id_if_needed(update)
        match update:
            case NewOrder():
                self.add_pending_order(update.to_order())
            case CancelOrder():
                self.update_active_order(
                    client_order_id=update.client_order_id,
                    order_id=update.order_id,
                    state=OrderState.CANCEL_PENDING,
                )
            case ModifyOrder():
                self.update_active_order(
                    order_id=update.order_id,
                    client_order_id=update.client_order_id,
                    state=OrderState.MODIFY_PENDING,
                )
            case OrderCancelUpdate():
                self.update_active_order(
                    order_id=update.order_id,
                    state=OrderState.CANCELLED,
                )
            case OrderUpdate():
                self.update_active_order(
                    order_id=update.order_id,
                    client_order_id=update.client_order_id,
                    state=OrderState.ACTIVE,
                    size=update.size,
                    filled_size=update.filled,
                    price=update.price,
                )

    def process_updates(
        self,
        updates: NewOrder
        | CancelOrder
        | ModifyOrder
        | OrderCancelUpdate
        | OrderUpdate
        | list[OrderUpdate]
        | list[OrderCancelUpdate],
    ):
        if not isinstance(updates, list):
            self.process_update(updates)
            return

        for update in updates:
            self.process_update(update)

    def add_pending_order(self, order: Order):
        if order.order_id in self.active_orders:
            raise ValueError(f"order with id {order.order_id} is already active")
        if order.order_id in self.done_orders:
            raise ValueError(f"order with id {order.order_id} is already done")

        self.active_orders[order.order_id] = order
        self.client_order_id_to_sender_id[order.order_id] = order.sender_id
        logger.info(f"added order {order.order_id}")

    def is_order_active(self, order_id: str) -> bool:
        return order_id in self.active_orders

    def is_order_done(self, order_id: str) -> bool:
        return order_id in self.done_orders

    def get_active_order(
        self,
        *,
        client_order_id: str | None = None,
        order_id: str | None = None,
    ) -> Order | None:
        if client_order_id:
            return self.active_orders.get(client_order_id)

        client_order_id = self.order_id_to_client_order_id.get(order_id)
        if client_order_id:
            return self.active_orders.get(client_order_id)

        return None

    def update_active_order(
        self,
        *,
        order_id: str | None = None,
        client_order_id: str | None = None,
        state: OrderState | None = None,
        filled_size: Decimal | None = None,
        size: Decimal | None = None,
        price: Decimal | None = None,
    ):
        if client_order_id:
            order_id_to_use = client_order_id
            if  order_id and (client_order_id not in self.order_id_to_client_order_id):
                self.order_id_to_client_order_id[order_id] = client_order_id
        else:
            order_id_to_use = self.order_id_to_client_order_id.get(order_id)

        if not order_id_to_use:
            # Order is unknown, we don't handle it.
            logger.warning(f"order with order_id:{order_id}/client_order_id:{client_order_id} is unknown, will not be modified")
            raise Exception()
            return

        order = self.active_orders.get(order_id_to_use)
        if not order:
            logger.warning(
                f"order with order_id:{order_id}/client_order_id:{client_order_id} is not active and cannot be modified"
            )
            raise Exception()
            return

        if state:
            order.state = state

        if filled_size:
            order.filled_size = filled_size

        if size:
            order.size = size

        if price:
            order.price = price

        if order.filled_size == order.size:
            order.state = OrderState.FILLED


        if order.state in [OrderState.FILLED, OrderState.CANCELLED]:
            self.done_orders[order_id_to_use] = order
            self.active_orders.pop(order_id_to_use)

