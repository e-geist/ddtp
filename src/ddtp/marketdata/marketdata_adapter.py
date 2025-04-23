from enum import Enum

from ddtp.api.kraken_derivatives.marketdata_adapter import (
    start_data_receival as kraken_deriv_data,
)


class AvailableMarketdataAdapter(Enum):
    KRAKEN_DERIVATIVES = kraken_deriv_data
