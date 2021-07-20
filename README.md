# Beacon Network

### Github Actions
[![CodeQL](https://github.com/CSCfi/beacon-network/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/CSCfi/beacon-network/actions/workflows/codeql-analysis.yml)
[![S2I Build](https://github.com/CSCfi/beacon-network/actions/workflows/.s2i-build.yml/badge.svg)](https://github.com/CSCfi/beacon-network/actions/workflows/.s2i-build.yml)
[![Style Checks](https://github.com/CSCfi/beacon-network/actions/workflows/.style.yml/badge.svg)](https://github.com/CSCfi/beacon-network/actions/workflows/.style.yml)
[![Registry Unit Tests](https://github.com/CSCfi/beacon-network/actions/workflows/.unit-reg.yml/badge.svg)](https://github.com/CSCfi/beacon-network/actions/workflows/.unit-reg.yml)
[![Aggregator Unit Tests](https://github.com/CSCfi/beacon-network/actions/workflows/.unit-agg.yml/badge.svg)](https://github.com/CSCfi/beacon-network/actions/workflows/.unit-agg.yml)
[![Documentation Checks](https://github.com/CSCfi/beacon-network/actions/workflows/.docs.yml/badge.svg)](https://github.com/CSCfi/beacon-network/actions/workflows/.docs.yml)

### External CI
[![Coverage Status](https://coveralls.io/repos/github/CSCfi/beacon-network/badge.svg?branch=master)](https://coveralls.io/github/CSCfi/beacon-network?branch=master)
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

## License

`beacon-network` and all it sources are released under *Apache 2.0 License*.