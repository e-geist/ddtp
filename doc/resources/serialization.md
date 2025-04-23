# What is it needed for?

> The process whereby an object or data structure is translated into a format suitable for transfer over a network, or storage (e.g. in an array buffer or file format).

https://developer.mozilla.org/en-US/docs/Glossary/Serialization (accessed 2025-03-09)

- transport between different processes or applications
- storing data
- examples: JSON, protobuf, msgpack, parquet, arrow (in-memory), pickle

# What do I need it for in a trading system?
- communication between decoupled system components
- storage of recorded data (e.g. market data)

# What do we need to pay attention at?
Different requirements for different use-cases

## Communication between decoupled system components
- De-/Serialization speed: very import -> how fast can it be processed?
- Storage size: mid important -> how much space does it take up in RAM + via network communication
- Standardized protocol: depends -> is the techstack rather broard or narrow? support for many languages needed?

## Storage of recorded data
Here everything depends on the data volume. 

Rather big data volume: recorded market data

Rather small data volume: compliance data (sent orders, trades)

- De-/Serialization speed: mid for recorded data (analysis) / not important for compliance data
- Storage size: very import for recorded data, because of huge volume / mid for compliance data
- Standardized protocol: important to enable analysis + evaluation via different systems

# Resources
- https://medium.com/@hugovs/the-need-for-speed-experimenting-with-message-serialization-93d7562b16e4
- https://medium.com/@shmulikamar/python-serialization-benchmarks-8e5bb700530b