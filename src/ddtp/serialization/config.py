from enum import StrEnum


class KafkaClusterEnvVars(StrEnum):
    BROKER = "KAFKA_BROKER"


class KafkaTopics(StrEnum):
    MARKETDATA = "marketdata"
    ORDER_ENTRY = "order_entry_send"
    ORDER_ENTRY_FEEDBACK = "order_entry_feedback"
