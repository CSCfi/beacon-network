#!/bin/bash

THE_HOST=${APP_HOST:="0.0.0.0"}
THE_PORT=${APP_PORT:="8080"}

if [ "$BEACON_RUN_APP" = "aggregator" ]; then
    echo 'Start Beacon Network Service: Aggregator'
    # exec beacon_aggregator
    exec gunicorn aggregator.aggregator:init_app --bind $THE_HOST:$THE_PORT --worker-class aiohttp.GunicornUVLoopWebWorker --workers 4
elif [ "$BEACON_RUN_APP" = "registry" ]; then
    echo 'Start Beacon Network Service: Registry'
    # exec beacon_registry
    exec gunicorn registry.registry:init_app --bind $THE_HOST:$THE_PORT --worker-class aiohttp.GunicornUVLoopWebWorker --workers 4
else
  echo "Set environment variable BEACON_RUN_APP to either 'registry' or 'aggregator'"
fi
