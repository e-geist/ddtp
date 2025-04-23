# What is storage of data needed for in a trading platform?
- storing actions that happened
  - compliance
  - component restarts
  - post trading analysis
- recording market data for analysis purposes

# What do we need to pay attention at?
Different requirements for different use-cases.

## Storing data for usage during live trading
- Speed: it must be fast - e.g. to save snapshots of component data for restarts
- Volume: data volume is not very big, as only most recent data is needed

-> Filestorage is too slow, we will use a RDBMS. As the de-facto standard, Postgres will be used - 
it should always be used, if there is no really big reason against it/ for something else.

It is sufficiently fast, has broad adaptation and libraries are available for all big programming languages.

## Storing data for usage outside live trading
- Speed: it must not be fast
- Volume: Big volume due to storing everything that happens (potentially forever)

-> Filestorage is fast enough in combination with parquet. (see [here for parquet](./serialization.md))

By using files in combination with parquet
- all common analytics systems will support reading and writing the data
- the data can be stored quite cheap forever in object (cold) storage

# Resources
- https://www.postgresql.org/
- https://parquet.apache.org/
- [object storage](https://www.druva.com/blog/object-storage-versus-block-storage-understanding-technology-differences)