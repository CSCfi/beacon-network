# Beacon Network APIs
Beacon Network is an ecosystem of registered Beacon services. The network consists of three different services; Registries, Aggregators and Beacons.

###  Registry
Beacon Registry `network-apis/registry.py` serves as a central storage of known Beacon services.

### Aggregator
Beacon Aggregator `network-apis/aggregator.py` serves as a query proxy that delegates user queries to multiple Beacons and returns the collected responses synchronously (http) or asynchronously (websocket).

### Beacon
[Beacon](https://github.com/CSCfi/beacon-python/) serves as a single queryable endpoint for data discovery. Standalone Beacons can be connected to Beacon Aggregators and Registries via service registration workflows.

##### Information
Dev Stage: [Implemented Endpoints](https://github.com/CSCfi/beacon-network/issues/1)

OAS3 Specification: [Beacon Network API](https://editor.swagger.io/?url=https://gist.githubusercontent.com/teemukataja/b583bd9c6c57afa9a04024f070c79a5b/raw/1b1eef9a8a538fd64f713a6ab3e562b382381ccd/beacon-network-specification-0_1.yml) (draft!)

Beacon Network: [Design Document](https://docs.google.com/document/d/1szKmxH0Ti8dcQ-CxKh9Iw5V3H6HuMYw4uYWb4Bynm9k)