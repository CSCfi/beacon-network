Beacon Network
==============

Beacon Network is a service for gathering multiple Beacons together for easy access. 

Beacon Network as a service consists of:

* A Registry for holding data regarding member Beacons
* An Aggregator that serves as a gateway to query all known Beacons at once
* A web portal that provides a GUI to use the APIs described above
* An OIDC client used for authenticating users and authorizing access to protected data

This documentation covers the configuration, installation and deployment of the Registry and Aggregator APIs.

For information regarding the other relevant service components, see:

* `OIDC Client <https://github.com/CSCfi/oidc-client>`_
* `Beacon Network UI <https://github.com/CSCfi/beacon-network-ui>`_

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2

   Configuration  <configuration>
   Setup          <setup>
   API            <api>
   Examples       <examples>
