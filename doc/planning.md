# Agenda

* Motivation  
* Fundamental trading concepts and market mechanics  
* Functional and non-functional requirements
* Market data ingestion and processing
* Order management and execution
* Implementation of trading strategies  
* Post-trade analysis  
* Outlook

# Motivation
* first and foremost: money
* access to markets is easier than ever (for crypto - this is also the reason we use crypto market here)
* everything in own hand
    * no subscription cost for trading system providers (but maybe for exchange + hardware)
    * more control -> adapt what is not like you want it
    * more flexibility
* interesting exercise with different technical challenges
* job opportunities

# Fundamental concepts
* What is trading?
* What is a market?
* What is trading on Orderbooks?
    * What is an Order? 
    * What is an Orderbook?
    * What is a trade?
    * What is a position?
* What is an exchange?
* What is algorithmic exchange trading?

# Functional and non-functional requirements
## Functional requirements
* I want to be able to trade goods with different algorithms on an exchange
* I want to get insights about how I traded
* I want to improve my trading systematically

## Nonfunctional requirements
* I want to trade on different exchanges and different exchanges have different protocols (Extensibility + Scalability)
* I want to trade multiple goods (Scalability)
* I want to use different algorithms for trading (Extensibility + Scalability)
* I need to have recordings about what actions were performed (Transparency + Compliance)
* I need to be sufficiently fast to be able to trade properly (Performance + Throughput)

## Resulting solution
* Trading algorithms must be decoupled from exchange interfaces
    * enables using multiple algorithms
    * enables trading on multiple exchanges
* Trading algorithms and exchange interfaces must be decoupled from traded goods
    * enables trading multiple goods
* Every action of an algorithm and on the exchange must be logged
    * enables complying to laws
    * enables to get insights about how trading went
    * enables systematical improvement of trading
* Bottlenecks must be kept to a minimum
    * enables trading to be sufficiently fast

TODO: Diagram?

# Implementation of trading strategies
TODO
# Market data ingestion and processing
TODO
# Order management and execution
TODO
# Post-trade analysis  
TODO
# Outlook