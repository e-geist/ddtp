# Why is communication between different components of the trading system needed?

Different components of the trading platform need to communicate because
- they are decoupled from each other (needed for extensibility and scalability)
- data needs to be saved for later use

# What do we need to pay attention at?
- Speed: it has to be sufficiently fast, without the receiver or sender waiting too long
- Reliability: it has to be reliable -> no UDP
- Support: it has to be supported by the languages we intend to use (in this case: Python) + not deprecated
- Communication over networks should be supported (so no UNIX sockets in this case, although they are very viable!)

# Possible candidates
*Decision*: 
In a real-world scenario probably kafka would be used for transferring big data volumes (e.g. marketdata), but
gRPC (or other protocol) for fast real-time communication between components. As this is a demo project, 
one solution was chosen for all needs: **kafka** due to
- better usability for marketdata recording (high-throughput needed) -> will sacrifice some latency
- better decoupling of components due to middleware and no point-to-point communication

## gRPC
https://grpc.io/
- Speed: very fast point to point communication
  - point-to-point connections -> horizontal scaling restricted but still possible
- Reliability: TCP - point to point connections
  - both sides have to be available during communication -> synchronous or near-synchronous
  - does not require any other middleware
  - request/response communication
- Support: supported by Google 
  - bindings available for all big programming languages
- requires protobuf
  - tight coupling of components
  - message structures need to be defined separately

## kafka
https://kafka.apache.org/
- Speed: low latency, but slower than grpc
    - can scale very nicely horizontally even with high data throughput
- Reliability: TCP - requires middleware/broker running that messages are produced to and consumed from
  - allows for different delivery modes (at least once, exactly once)
  - async: receiver has not to be up when message is sent + messages can be repeated
- Support: supported by Confluent
  - producer/consumer libraries available for all big programming languages
- requires running middleware 
- supports any format for messages

## Proprietary protocol on top of TCP
- not considered due to effort + maintenance here

## Unix sockets
- not considered here due to network requirement

# Resources
- https://medium.com/mcmc-targeted-advertisements/choosing-between-grpc-and-kafka-7ecf5981f988
- https://risingwave.com/blog/kafka-vs-grpc-which-is-right-for-you/
- https://grpc.io/
- https://kafka.apache.org/