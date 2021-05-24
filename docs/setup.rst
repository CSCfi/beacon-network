Installation and Deployment
===========================

Instructions for setting up the Aggregator and Registry APIs and their database.

.. note::

  APIs and database can be set up in containers or locally. Requirements for installation:

  Containerised
    * Docker

  Local
    * Python 3.8+
    * PostgreSQL 12.6+

Installation
~~~~~~~~~~~~

Install both Aggregator and Registry APIs with a single command.

.. code-block:: console

    git clone https://github.com/CSCfi/beacon-network
    cd beacon-network
    pip install .

The APIs can then be run with the following commands:

.. code-block:: console

    # Run aggregator
    beacon_aggregator

    # Run registry
    beacon_registry

This starts the web applications with ``aiohttp.web.run_app`` using aiohttp's default server.
This is a lightweight way to run the apps, but for more stability see the Production Server section below.

Development Server
~~~~~~~~~~~~~~~~~~

For development, both APIs can be run withouth installation using aiohttp's default ``web.run_app`` method.

.. code-block:: console

    cd beacon-network
    # If running without installation, install modules first
    pip install -r requirements.txt

    # Run aggregator
    python -m aggregator.aggregator

    # Run Registry
    python -m registry.registry

Production Server
~~~~~~~~~~~~~~~~~

For production it is recommended to use `gunicorn <https://gunicorn.org/>`_ instead of aiohttp's default server for stability.

Environment variables ``APP_HOST`` and ``APP_PORT`` can be used to designate a hostname.

.. code-block:: console

    # Run aggregator
    gunicorn aggregator.aggregator:init_app --bind $APP_HOST:$APP_PORT \
                                            --worker-class aiohttp.GunicornUVLoopWebWorker \
                                            --workers 4

    # Run registry
    gunicorn registry.registry:init_app --bind $APP_HOST:$APP_PORT \
                                        --worker-class aiohttp.GunicornUVLoopWebWorker \
                                        --workers 4

Image Building
~~~~~~~~~~~~~~

Aggregator and Registry can also be built into an image and then be deployed.
First build the image. The same base image will be used for both services.

Either ``s2i`` or ``docker`` can be used to build an image from the source code.
``s2i`` builds very quickly, but is rather large in size ~700MB. ``docker`` builds the image with
``Dockerfile`` and results in an image roughly half the size of ``s2i`` at ~370MB, but takes considerably longer to build.

.. code-block:: console

  # Build using s2i
  s2i build . centos/python-36-centos7 cscfi/beacon-network

  # Build using docker
  docker build -t cscfi/beacon-network .

Manual Container Deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run the images with docker, specifying which service to run with the environment variable ``BEACON_RUN_APP``
which can take only two distinct values: ``aggregator`` and ``registry``.

.. code-block:: console

    # Run aggregator
    docker run -d -p 8080:8080 -e BEACON_RUN_APP=aggregator cscfi/beacon-network

    # Run registry
    docker run -d -p 8080:8080 -e BEACON_RUN_APP=registry cscfi/beacon-network

Other environment variables can also be passed here to overwrite the values given in the configuration file.

Database Container
~~~~~~~~~~~~~~~~~~

.. note::

    The Registry API is dependent on a PostgreSQL database. This can be easily set up in a container as well.
    The created database will be populated with the ``init.sql`` located at ``registry/db``.

.. code-block:: console

    cd beacon-network/registry/db
      docker run -d --name registry-db \
      -e POSTGRES_USER=user \
      -e POSTGRES_PASSWORD=pass \
      -e POSTGRES_DB=registry \
      -v "$PWD"/docker-entrypoint-initdb.d/:/docker-entrypoint-initdb.d/ \
      -p 5432:5432 postgres:12.6

Docker Compose Deployment
~~~~~~~~~~~~~~~~~~~~~~~~~

``docker-compose`` can be leveraged to launch both Aggregator and Registry APIs with a database for Registry simultaneously.

Simply:

.. code-block:: console

  docker-compose up

.. note::

    The image must be built with ``docker`` in order for this to work, see Image Building section above.
