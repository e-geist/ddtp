# What is it needed for?

> The process whereby an object or data structure is translated into a format suitable for transfer over a network, or storage (e.g. in an array buffer or file format).

https://developer.mozilla.org/en-US/docs/Glossary/Serialization (accessed 2025-03-09)

- transport between different processes or applications
- storing data
- examples: JSON, protobuf, msgpack, SBE, flatbuffers, parquet, arrow (in-memory), pickle

# What do I need it for in a trading system?
Main use cases:
- Communication in live trading system between components
- Storage of offline data

# What do we need to pay attention at?
Different requirements for different use-cases. 

## Communication between decoupled system components
- De-/Serialization speed: very import -> how fast can it be processed?
- Data size: mid important -> how much space does it take up in RAM + via network communication
- Standardized protocol: depends -> is the techstack rather broad or narrow? support for many languages needed?

*Decision*: **msgpack** due to better language support for Python + decision against gRPC (otherwise protobuf
would have been needed)

### JSON
Too big and too slow in serialization and deserialization.

### Protocol buffers (protobuf)
https://protobuf.dev/
- by Google
- good language support (all big programming languages)
- has schema -> definition of objects in fbs file and compilation to python objects
- serialization used in gRPC
- slower compared to flatbuffers, faster than JSON and msgpack

### Flatbuffers
https://flatbuffers.dev
- by Google
- good language support (all big programming languages)
- has schema -> definition of objects in proto file and compilation to python objects
- faster than protobuf

### Msgpack
https://msgpack.org/
- backed and used by big products like redis, fluentd, pinterest
- schemaless
- good language support (all big programming languages)
- [ormsgpack](https://github.com/aviramha/ormsgpack) has good "Pythonic" support (dataclasses, tuples, lists,..)

## Storage of recorded data
Here everything depends on the data volume. 

Rather big data volume: recorded market data

Rather small data volume: compliance data (sent orders, trades)

- De-/Serialization speed: mid for recorded data (analysis) / not important for compliance data
- Data size: very import for recorded data, because of huge volume / mid for compliance data
- Standardized protocol: important to enable analysis + evaluation via different systems


*Decision*: De-facto standard [**parquet**](https://parquet.apache.org/) due to very good support in all systems, 
versatility, space and speed. On top of parquet of course some table-format can (and probably should!) be used, 
like Apache Iceberg or Delta Lake. As this is a demo project, these were omitted.

# Resources
- https://medium.com/@hugovs/the-need-for-speed-experimenting-with-message-serialization-93d7562b16e4
- https://medium.com/@shmulikamar/python-serialization-benchmarks-8e5bb700530b
- https://protobuf.dev/
- https://flatbuffers.dev/benchmarks/
- https://msgpack.org/
- https://github.com/aviramha/ormsgpack
- https://parquet.apache.org/