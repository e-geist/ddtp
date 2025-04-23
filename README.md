# ddtp
DIY Distributed Trading Platform

# What is this?
This is a proof of concept implementation of a distributed trading platform/system using only open source technologies.
It was implemented as a complement to a talk at PyconDE2025.

# Which exchanges are supported?
So far only the [Kraken derivatives exchange](https://support.kraken.com/hc/en-us/sections/360012894412-Futures-API)
is implemented and supported.

# What technologies are used?
- Python3.13 + libraries (see [pyproject.toml](./pyproject.toml) for details)
- Kafka for component communication
- uv as build system
- docker for test containers

# How to use

## Pre-requisites

* [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
* [have docker compose installed](https://docs.docker.com/compose/install/), if you want to use the provided kafka container
* Get API key and secret for Kraken futures
  * sign up at Kraken futures - e.g. at the [demo environment](https://demo-futures.kraken.com/futures)
  * [create and retrieve API key + secret](https://support.kraken.com/hc/en-us/articles/360022839451-How-to-create-an-API-key-for-Kraken-Futures)
* create .env file based on [.env_template](./.env_template) and fill details
  * base urls depending on the environment you use ([see here](https://support.kraken.com/hc/en-us/articles/360024809011-API-Testing-Environment) for details)
  * API key and secret from previous step
  * URL of Kafka broker - if you're using the provided container, keep `localhost:9092`

## Run 

* [optional] run docker compose file for kafka container: `docker compose -f docker/docker-compose.yml up` or `make start-kafka`
* run marketdata provider: `uv run marketdata_provider`
* run order excecution engine: `uv run order_execution_engine`
* run example strategy: `uv run buy_on_small_spread_strategy`

# More details
If you want to learn more about the structure and decisions made, have a look at the [presentation](./doc/presentation/presentation.html).