Examples
========

The following examples have been conducted against live APIs.

Aggregator Examples
-------------------

The Aggregator serves as a single querying point that propagates the user query to multiple Beacons, and aggregates their responses.

Get API Info
~~~~~~~~~~~~

API info is requested with ``GET`` method from the ``/service-info`` endpoint. The response follows `GA4GH Service Info <https://github.com/ga4gh-discovery/ga4gh-service-info>`_ specification.

Request
^^^^^^^

.. code-block:: console

    curl localhost:5000/service-info

Response
^^^^^^^^

.. code-block:: javascript

    {
        "id": "localhost:5000",
        "name": "ELIXIR-FI Beacon Aggregator",
        "type": "urn:ga4gh:aggregator",
        "description": "ELIXIR-FI Beacon Aggregator at CSC for Beacon network",
        "documentationUrl": "https://beacon-network.readthedocs.io/en/latest/",
        "organization": "fi.csc",
        "contactUrl": "https://www.csc.fi/contact-info",
        "apiVersion": "0.3.0",
        "version": "0.2.dev",
        "extension": {}
    }

Query Beacons
~~~~~~~~~~~~~

Beacons are queried with ``GET`` method from the ``/query`` endpoint. The response follows `GA4GH Beacon <https://github.com/ga4gh-beacon/specification/>`_ specification. The response is an array of these objects.
The Aggregator can be queried synchronously with ``HTTPS`` and asynchronously with ``WSS`` (websocket).

Request
^^^^^^^

Standard HTTP query with synchronous answer

.. code-block:: console

    curl localhost:5000/query?assemblyId=GRCh38&referenceName=MT&start=9&referenceBases=T&alternateBases=C

For a websocket query, the following headers are required: ``Connection: Upgrade`` and ``Upgrade: Websocket``. The requester should be a websocket client capable of receiving the data stream.

Response
^^^^^^^^

.. code-block:: javascript

    [
        {
            "beaconId": "se.nbis.swefreq",
            "apiVersion": "1.1.0",
            "exists": false,
            "alleleRequest": {
                "referenceName": "MT",
                "referenceBases": "T",
                "assemblyId": "GRCh38",
                "includeDatasetResponses": "NONE",
                "alternateBases": "C",
                "start": 9
            },
            "datasetAlleleResponses": [],
            "beaconHandover": []
        },
        {
            "beaconId": "fi.rahtiapp.beaconpy-elixirbeacon",
            "apiVersion": "1.1.0",
            "exists": true,
            "alleleRequest": {
                "referenceName": "MT",
                "referenceBases": "T",
                "assemblyId": "GRCh38",
                "includeDatasetResponses": "NONE",
                "alternateBases": "C",
                "start": 9
            },
            "datasetAlleleResponses": []
        },
        {
            "beaconId": "fi.rahtiapp.staging-elixirbeacon",
            "apiVersion": "1.1.0",
            "exists": true,
            "alleleRequest": {
                "referenceName": "MT",
                "referenceBases": "T",
                "assemblyId": "GRCh38",
                "includeDatasetResponses": "NONE",
                "alternateBases": "C",
                "start": 9
            },
            "datasetAlleleResponses": []
        }
    ]

Delete Cached Beacons
~~~~~~~~~~~~~~~~~~~~~

Aggregator cache is deleted with ``DELETE`` method from the ``/cache`` endpoint. This endpoint is protected with a header API key named ``Authorization``.
This key is read from the ``registries.json`` file from the ``key`` key. More information below.

When the Aggregator is queried, the Aggregator requests a list of Beacons from a pre-configured Registry. This list is then cached for one hour for sequential queries.
Should the service catalogue at the Registry change, a new list of Beacons should be supplied to the Aggregator. Registries can automatically call this endpoint
if the Aggregator has been registered at the Registry, and the Aggregator has saved the service key to its ``registries.json`` in they ``key`` key.

.. literalinclude:: ../aggregator/config/registries.json
   :language: javascript
   :lines: 1-6

Request
^^^^^^^

.. code-block:: console

    curl -x DELETE \
         localhost:5000/cache \
         -H 'Authorization: secret'

Response
^^^^^^^^

.. code-block:: javascript

    Cache has been deleted.

Registry Examples
-----------------

The Registry serves as a central hub of known Beacons. The Aggregator utilises this catalogue for queries.

Get API Info
~~~~~~~~~~~~

API info is requested with ``GET`` method from the ``/service-info`` endpoint. The response follows `GA4GH Service Info <https://github.com/ga4gh-discovery/ga4gh-service-info>`_ specification.

Request
^^^^^^^

.. code-block:: console

    curl localhost:8080/service-info

Response
^^^^^^^^

.. code-block:: javascript

    {
        "id": "localhost:8080",
        "name": "ELIXIR-FI Beacon Registry",
        "type": "urn:ga4gh:registry",
        "description": "ELIXIR-FI Beacon Registry at CSC for Beacon network",
        "documentationUrl": "https://beacon-network.readthedocs.io/en/latest/",
        "organization": "fi.csc",
        "contactUrl": "https://www.csc.fi/contact-info",
        "apiVersion": "0.3.0",
        "version": "0.2.dev",
        "extension": {}
    }

List Service Types
~~~~~~~~~~~~~~~~~~

Service types are requested with ``GET`` method from the ``/services/types`` endpoint.

Request
^^^^^^^

.. code-block:: console

    curl localhost:8080/services/types

Response
^^^^^^^^

.. code-block:: javascript

    [
        "urn:ga4gh:registry",
        "urn:ga4gh:aggregator",
        "urn:ga4gh:beacon"
    ]

List Service Statuses
~~~~~~~~~~~~~~~~~~~~~

Service statuses are listed with ``GET`` method from the ``/services/status`` endpoint. This endpoint has not yet been implemented.

Request
^^^^^^^

.. code-block:: console

    curl localhost:8080/services/status

Response
^^^^^^^^

.. code-block:: javascript

    405: Not Implemented


Register a New Service
~~~~~~~~~~~~~~~~~~~~~~

A new service can be registered with ``POST`` method at the ``/services`` endpoint. This endpoint is protected with a header API key named ``Authorization``.
This key is read from the database table ``api_keys``.

The registration process requires a maintainer email address, URL to service info endpoint and type of service. The Registry then attempts to pull the
service information from the given URL. The endpoint should follow either `GA4GH Beacon API specification <https://github.com/ga4gh-beacon/specification/>`_ ``/`` or `GA4GH Service Info specification <https://github.com/ga4gh-discovery/ga4gh-service-info>`_ ``/service-info``.

Request
^^^^^^^

.. code-block:: console

    curl -X POST \
    localhost:8080/services \
    -H 'Authorization: secret' \
    -d '{
        "email": "support@csc.fi",
        "type": "urn:ga4gh:beacon",
        "url": "localhost:3000/"
    }'

Response
^^^^^^^^

.. code-block:: javascript

    {
        "message": "Service has been registered. Service key and id for updating and deletingregistration included in this response, keep them safe.",
        "serviceId": "localhost:3000",
        "serviceKey": "secret",
        "help": "https://beacon-network.readthedocs.io/en/latest/"
    }

List Registered Services
~~~~~~~~~~~~~~~~~~~~~~~~

Services can be listed with ``GET`` method on the ``/services`` endpoint.

Request
^^^^^^^

.. code-block:: console

    curl localhost:8080/services

Response
^^^^^^^^

.. code-block::  javascript

    [
        {
            "id": "fi.rahtiapp.staging-elixirbeacon",
            "name": "GA4GHBeacon at CSC",
            "type": "urn:ga4gh:beacon",
            "description": "Beacon API Web Server based on the GA4GH Beacon API",
            "url": "https://staging-elixirbeacon.rahtiapp.fi/",
            "createdAt": "2019-07-25 10:57:34.238533+00:00",
            "updatedAt": "2019-08-02 00:00:13.006256+00:00",
            "contactUrl": "https://www.csc.fi/contact-info",
            "apiVersion": "1.1.0",
            "version": "1.4.0",
            "extension": {
                "achievement": "World's first 1.0 Beacon",
                "organization": {
                    "name": "CSC - IT Center for Science",
                    "logoUrl": "https://www.csc.fi/documents/10180/161914/CSC_2012_LOGO_RGB_72dpi.jpg",
                    "welcomeUrl": "https://www.csc.fi/"
                }
            }
        },
        {
            "id": "fi.rahtiapp.beaconpy-elixirbeacon",
            "name": "GA4GHBeacon at CSC",
            "type": "urn:ga4gh:beacon",
            "description": "Beacon API Web Server based on the GA4GH Beacon API",
            "url": "https://beaconpy-elixirbeacon.rahtiapp.fi/",
            "createdAt": "2019-07-25 10:57:28.863961+00:00",
            "updatedAt": "2019-08-02 00:00:13.016122+00:00",
            "contactUrl": "https://www.csc.fi/contact-info",
            "apiVersion": "1.1.0",
            "version": "1.4.0",
            "extension": {
                "achievement": "World's first 1.0 Beacon",
                "organization": {
                    "name": "CSC - IT Center for Science",
                    "logoUrl": "https://www.csc.fi/documents/10180/161914/CSC_2012_LOGO_RGB_72dpi.jpg",
                    "welcomeUrl": "https://www.csc.fi/"
                }
            }
        },
        {
            "id": "fi.rahtiapp.dev-aggregator-beacon",
            "name": "ELIXIR-FI Beacon Aggregator",
            "type": "urn:ga4gh:aggregator",
            "description": "ELIXIR-FI Beacon Aggregator at CSC for Beacon network",
            "url": "https://dev-aggregator-beacon.rahtiapp.fi/service-info",
            "createdAt": "2019-07-25 10:57:11.340018+00:00",
            "updatedAt": "2019-08-05 00:00:10.960787+00:00",
            "contactUrl": "https://www.csc.fi/contact-info",
            "apiVersion": "0.3.0",
            "version": "0.2.dev",
            "extension": {
                "logoUrl": "https://www.csc.fi/csc-subpage-theme/images/csc-logo-teksti-en.png"
            }
        }
    ]

Find Service by ID
~~~~~~~~~~~~~~~~~~

A specific service can be found with ``GET`` method on the ``/services`` endpoint by supplying the service ID as a path parameter in ``/services/<id>``.

Request
^^^^^^^

.. code-block:: console

    curl localhost:8080/services/fi.rahtiapp.beaconpy-elixirbeacon

Response
^^^^^^^^

.. code-block:: javascript

    {
        "id": "fi.rahtiapp.staging-elixirbeacon",
        "name": "GA4GHBeacon at CSC",
        "type": "urn:ga4gh:beacon",
        "description": "Beacon API Web Server based on the GA4GH Beacon API",
        "url": "https://staging-elixirbeacon.rahtiapp.fi/",
        "createdAt": "2019-07-25 10:57:34.238533+00:00",
        "updatedAt": "2019-08-02 00:00:13.006256+00:00",
        "contactUrl": "https://www.csc.fi/contact-info",
        "apiVersion": "1.1.0",
        "version": "1.4.0",
        "extension": {
            "achievement": "World's first 1.0 Beacon",
            "organization": {
                "name": "CSC - IT Center for Science",
                "logoUrl": "https://www.csc.fi/documents/10180/161914/CSC_2012_LOGO_RGB_72dpi.jpg",
                "welcomeUrl": "https://www.csc.fi/"
            }
        }
    }

Update Service
~~~~~~~~~~~~~~

An existing service can be updated with ``PUT`` method at the ``/services`` endpoint with the service ID specified as a path parameter ``/service/<id>``.
This endpoint is protected with a header API key named ``Beacon-Service-Key`` which was given to the registrar at registration.
This key is read from the database table ``service_keys``.

The update process follows the same principles as the registration process.

Request
^^^^^^^

.. code-block:: console

    curl -X PUT \
    localhost:8080/services/localhost:3000 \
    -H 'Beacon-Service-Key: secret' \
    -d '{
        "email": "support@csc.fi",
        "type": "urn:ga4gh:beacon",
        "url": "localhost:3000/"
    }'

Response
^^^^^^^^

.. code-block:: javascript

    Service has been updated.

Delete Service
~~~~~~~~~~~~~~

A registered service can be deleted from the Registry with ``DELETE`` method on the ``/services`` endpoint with the service ID specified as a path parameter ``/service/<id>``.
This endpoint is protected with header ``Beacon-Service-Key`` which was given to the registrar at registration.

Request
^^^^^^^

.. code-block:: console

    curl -X DELETE \
    localhost:8080/services/localhost:3000 \
    -H 'Beacon-Service-Key: secret'

Response
^^^^^^^^

.. code-block:: javascript

    Service has been deleted.

Update Service Catalogue
~~~~~~~~~~~~~~~~~~~~~~~~

The whole service catalogue at a Registry can be updated with ``GET`` method on the ``/update/services`` endpoint.  This endpoint is protected with a header API key named ``Authorization``.
This key is read from the database table ``admin_keys``.

This event will trigger the Registry to fetch up-to-date information frmo all registered services and to update the database accordingly.

Request
^^^^^^^

.. code-block:: console

    curl -X GET \
    localhost:8080/update/services \
    -H 'Authorization: secret'

Response
^^^^^^^^

.. code-block:: javascript

    3 successful update(s). 0 failed update(s).
