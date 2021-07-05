#!/bin/bash

AGGREGATOR="http://localhost:5050"
REGISTRY="http://localhost:8080"

docker exec -i beacon-network_db_registry_1 psql -U user -d registry < ./tests/test_files/testApiKeys.sql

curl -X 'POST' \
    "${REGISTRY}/services" \
    -H 'Authorization: 07b4e8ed58a6f97897b03843474c8cc981d154ffe45b10ef88a9f127b15c5c56' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "type": "beacon",
    "url": "https://staging-elixirbeacon.rahtiapp.fi/service-info"
    }'

curl -X 'POST' \
    "${REGISTRY}/services" \
    -H 'Authorization: 07b4e8ed58a6f97897b03843474c8cc981d154ffe45b10ef88a9f127b15c1234' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "type": "beacon-aggregator",
    "url": "http://app_aggregator:5050/service-info"
    }'
