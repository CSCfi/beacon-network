# Archival Notice
`beacon-network` was developed for ELIXIR Beacon implementation studies [2018](https://elixir-europe.org/internal-projects/commissioned-services/beacon-network-service) and [2019-2021](https://elixir-europe.org/internal-projects/commissioned-services/beacon-2019-21). Development on the Beacon v1 specification has ceased, and a new Beacon v2 specification has been finalised, and is being adopted by beacon providers.

Users are encouraged to move to the next iteration of [Beacon Network v2](https://github.com/elixir-europe/beacon-network-backend). Beacon v2 development can be followed at [GA4GH Beacon v2 Project](https://beacon-project.io/).

We thank all parties that have been involved with us in the development of the Beacon v1 products past these years.

## Beacon Network

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