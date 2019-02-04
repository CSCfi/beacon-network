#!/bin/bash

if [ "$BEACON_RUN_APP" = "registry" ]; then
    echo 'Start Beacon Network: Aggregator'
    exec beacon_aggregator
elif [ "$BEACON_RUN_APP" = "aggregator" ]; then
    echo 'Start Beacon Network: Registry'
    exec beacon_registry
else
  echo "Set environment variable BEACON_RUN_APP to either 'registry' or 'aggregator'"
fi
