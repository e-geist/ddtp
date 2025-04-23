from enum import Enum
from ddtp.api.kraken_derivatives.execution_engine_adapter import (
    start_feedback_data_receival as kraken_deriv_feedback,
    process_order_action as kraken_deriv_send_action,
)


class AvailableExecutionEngineAdapter(Enum):
    KRAKEN_DERIVATIVES = (kraken_deriv_feedback, kraken_deriv_send_action)
