# Beacon Network APIs
Beacon Network is an ecosystem of registered Beacon services. The network consists of three different services; Registries, Aggregators and Beacons.

###  Registry
Beacon Registry `network-apis/registry.py` serves as a central storage of known Beacon services.

### Aggregator
Beacon Aggregator `network-apis/aggregator.py` serves as a query proxy that delegates user queries to multiple Beacons and returns the collected responses synchronously (http) or asynchronously (websocket).

### Beacon
[Beacon](https://github.com/CSCfi/beacon-python/) serves as a single queryable endpoint for data discovery. Standalone Beacons can be connected to Beacon Aggregators and Registries via service registration workflows.
