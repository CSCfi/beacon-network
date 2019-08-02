# Beacon Network

[![Build Status](https://travis-ci.org/CSCfi/beacon-network.svg?branch=master)](https://travis-ci.org/CSCfi/beacon-network)
[![Documentation Status](https://readthedocs.org/projects/beacon-network/badge/?version=latest)](https://beacon-network.readthedocs.io/en/latest/?badge=latest)

Beacon Network is a service for gathering multiple Beacons together for easy access. 

Beacon Network as a service consists of:

* A Registry for holding data regarding member Beacons
* An Aggregator that serves as a gateway to query all known Beacons at once
* A web portal that provides a GUI to use the APIs described above
* An OIDC client used for authenticating users and authorizing access to protected data

This repository covers Aggregator and Registry APIs.

For information regarding the other relevant service components, see:

* [OIDC Client](https://github.com/CSCfi/oidc-client)
* [Beacon Network UI](https://github.com/CSCfi/beacon-network-ui)

## Documentation

For instructions on configuring and setting up Registry and Aggregator APIs, refer to the [documentation](https://beacon-network.readthedocs.io/).
