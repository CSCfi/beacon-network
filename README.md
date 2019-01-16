# Beacon Network APIs

WIP

###  Registry
Beacon Registry `network-apis/registry.py` serves as a central storage of known Beacon services.

### Aggregator
Beacon Aggregator `network-apis/aggregator.py` serves as a query proxy that delegates user queries to multiple Beacons and returning the collected responses synchronously (http) or asynchronously (websocket).

### Beacon
[Beacon](https://github.com/CSCfi/beacon-python/) serves as a single queryable endpoint for data discovery. Standalone Beacons can be connected to Beacon Aggregators and Registries via service registration workflows.

##### Information
OAS3 Specification: [Beacon Network API](https://editor.swagger.io/?url=https://gist.githubusercontent.com/teemukataja/b583bd9c6c57afa9a04024f070c79a5b/raw/35ebb359ed18c81d48c3b334e259c78a050b8e8e/beacon-network-specification-0_1.yml) (draft!)

Beacon Network: [Design Document](https://docs.google.com/document/d/1szKmxH0Ti8dcQ-CxKh9Iw5V3H6HuMYw4uYWb4Bynm9k)