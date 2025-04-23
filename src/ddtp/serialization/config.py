from enum import StrEnum


class KafkaClusterEnvVars(StrEnum):
    BROKER = "KAFKA_BROKER"

class KafkaTopics(StrEnum):
    MARKETDATA = "marketdata"
