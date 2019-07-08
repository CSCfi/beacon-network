# Beacon Network APIs
Beacon Network is an ecosystem of registered Beacon services. The network consists of three different services; Registries, Aggregators and Beacons.

## APIs

###  Registry
Beacon Registry `registry/registry.py` serves as a central storage of known Beacon services.

### Aggregator
Beacon Aggregator `aggregator/aggregator.py` serves as a query proxy that delegates user queries to multiple Beacons and returns the collected responses synchronously (http) or asynchronously (websocket).

### Beacon
[Beacon](https://github.com/CSCfi/beacon-python/) serves as a single queryable endpoint for data discovery. Standalone Beacons can be connected to Beacon Aggregators and Registries via service registration workflows.

## UI

### Beacon Network UI
Beacon Network APIs are served through a [User Interface](https://github.com/CSCfi/beacon-network-ui). Queries made from Beacon Network UI are proxied to an Aggregator, which propagates the variant request to registered Beacons.

### Beacon Login
The Beacon Network UI above relies on external AAIs for authentication of users and authorisation of access to datasets. The AAI client can be found [here](https://github.com/CSCfi/oidc-client).
