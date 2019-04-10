Setup
=====

Setup instructions for different services.

APIs
----

Instructions for setting up the Registry and Aggregator APIs and their databases.

.. note::

  System requirements

  Containerised
    * Docker

  Or

  Local
    * Python 3.6+
    * PostgreSQL 9.6+

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Registry and Aggregator are very similar in structure, and as such, they share the same environment variable names (but when separated with an environment or container, they can be assigned different values).

Configuration priority flows as follows: ENV > CONFIG FILE > DEFAULT. If no values are set, defaults are assumed. You can write persistent configuration in ``/network_apis/config/config.ini``. Values set for environment variables will overwrite values written in the configuration file.

+-----------------------+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ENV                   | Default        | Description                                                                                                                                                                       |
+=======================+================+===================================================================================================================================================================================+
| CONFIG_FILE           | config.ini     | Location of configuration file, absolute path.                                                                                                                                    |
+-----------------------+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| BEACON_RUN_APP        |                | Specify which app to run inside a container. Possible values: registry and aggregator.                                                                                            |
+-----------------------+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| DEBUG                 | False          | Set to True to enable more debugging logs from functions.                                                                                                                         |
+-----------------------+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| HOST_ID               |                | Unique service ID for this service, refers to services.id in the database. (the host's service info is stored in the database along with infos from all other connected services) |
+-----------------------+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| DB_HOST               | localhost      | Database address.                                                                                                                                                                 |
+-----------------------+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| DB_PORT               | 5432           | Database port.                                                                                                                                                                    |
+-----------------------+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| DB_USER               | user           | Username to access database.                                                                                                                                                      |
+-----------------------+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| DB_PASS               | pass           | Password for database user.                                                                                                                                                       |
+-----------------------+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| DB_NAME               | db             | Database name.                                                                                                                                                                    |
+-----------------------+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| APP_HOST              | 0.0.0.0        | Application hostname.                                                                                                                                                             |
+-----------------------+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| APP_PORT              | 8080           | Application port.                                                                                                                                                                 |
+-----------------------+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| APPLICATION_SECURITY  |                | Application security level, determines the SSL operating principle of the server. Possible values are 0-2, more information in SSL Context section below.                         |
+-----------------------+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| REQUEST_SECURITY      |                | Request security level, determines the SSL operating principle of requests. Possible values are 0-2, more information in SSL Context  section below.                              |
+-----------------------+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| PATH_SSL_CERT_FILE    | /etc/ssl/certs | Path to certificate.pem file.                                                                                                                                                     |
+-----------------------+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| PATH_SSL_KEY_FILE     | /etc/ssl/certs | Path to key.pem file.                                                                                                                                                             |
+-----------------------+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| PATH_SSL_CA_FILE      | /etc/ssl/certs | Path to ca.pem file.                                                                                                                                                              |
+-----------------------+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Possible security levels for ``APPLICATION_SECURITY`` and ``REQUEST_SECURITY`` are 0-2.

+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------+
| Security Level | APPLICATION_SECURITY Behaviour                                                                                                                                                              | REQUEST_SECURITY Behaviour                                                                                                |
+================+=============================================================================================================================================================================================+===========================================================================================================================+
| 0              | Application is unsafe. API is served as HTTP.                                                                                                                                               | Application can make requests to HTTP (unsafe) and HTTPS (safe) resources.                                                |
+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------+
| 1              | Application is safe. API is served as HTTPS. This requires the use of PATH_SSL_* ENVs.                                                                                                      | Application can only make requests to HTTPS (safe) resources. Requests to HTTP (unsafe) resources are blocked.            |
+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------+
| 2              | Application belongs to a closed trust network. Applies same behaviour as security level 1. Application can only be requested from other applications that belong to the same trust network. | Application can only make requests to applications that belong to the same trust network (see previous cell description). |
+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------+

As a rule of thumb, security level 0 can be used in testing and development. Security level 1 should always be used as a minimum security level for publicly available services. Security level 2 is a special case for services in closed trust network (certificate sharing).

Automatic Setup
~~~~~~~~~~~~~~~

Registry and Aggregator databases and APIs can be set up automatically by leveraging ``docker-compose``. To set up services automatically, first build images and then compose them.

.. code-block:: console

  cd network_apis
  docker build -t cscfi/beacon-network .
  docker-compose up

This process will start four containers:

* Registry API `(start by default at localhost:3000)`
* Registry DB
* Aggregator API `(starts by default at localhost:3001)`
* Aggregator DB

Database containers are linked directly to their respective API containers, and as such, database ports don't need to be worried about. For modifying the hosts, ports and ENVs refer to the ``/network_apis/docker-compose.yml`` file.

Manual Setup
~~~~~~~~~~~~

The services can also be set up manually, for e.g. faster development/testing cycle.

If you are using a local PostgreSQL server, you can generate tables with ``/network_apis/db/docker-entrypoint-initdb.d/init.sql``. To more easily set up a database, you can spin up a PostgreSQL container in docker and populate it automatically.

To set up database containers for both Registry and Aggregator respectively, you can do:

.. code-block:: console

  cd db
  docker run -d \
  -e POSTGRES_USER=reg_user \
  -e POSTGRES_PASSWORD=reg_pass \
  -e POSTGRES_DB=reg_db \
  -v "$PWD"/docker-entrypoint-initdb.d/:/docker-entrypoint-initdb.d/ \
  -p 5438:5432 postgres:9.6

  docker run -d \
  -e POSTGRES_USER=agg_user \
  -e POSTGRES_PASSWORD=agg_pass \
  -e POSTGRES_DB=agg_db \
  -v "$PWD"/docker-entrypoint-initdb.d/:/docker-entrypoint-initdb.d/ \
  -p 5439:5432 postgres:9.6

This will start database containers at ``localhost:5438`` and ``localhost:5439`` for Registry and Aggregator respectively.

To run the applications manually you have three options: python module command, install python modules and run, build containers and run.

To run APIs without installing:

.. code-block:: console

  git clone https://github.com/CSCfi/beacon-network/
  cd beacon-network/network_apis
  pip install -r requirements.txt
  python3 -m registry    # starts registry
  python3 -m aggregator  # starts aggregator

To install APIs and run:

.. code-block:: console

  git clone https://github.com/CSCfi/beacon-network/
  cd beacon-network/network_apis
  pip install .
  beacon_registry    # starts registry
  beacon_aggregator  # starts aggregator

To build containers and run:

.. code-block:: console

  # Using s2i
  cd network_apis
  s2i build . centos/python-36-centos7 cscfi/beacon-network

  # Or using docker
  cd network_apis
  docker build -t cscfi/beacon-network .

  docker run -d -e BEACON_RUN_APP=registry cscfi/beacon-network      # starts registry
  docker run -d -e BEACON_RUN_APP=aggregator cscfi/beacon-network    # starts aggregator

These commands will start the APIs at ``localhost:3000`` and ``localhost:3001`` for Registry and Aggregator respectively.

GUI
---

Instructions for setting up the GUI (website) and ELIXIR AAI login client.

.. note::

  System requirements

  Containerised
    * Docker

  Or

  Local
    * Python 3.6+
    * A web server, e.g. Apache, NodeJS...

`TO DO: DOCS FOR GUI`