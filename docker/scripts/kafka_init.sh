#!/bin/sh

/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:19092 --create --topic marketdata
/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:19092 --create --topic order_entry_send
/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:19092 --create --topic order_entry_feedback