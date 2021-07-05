#!/bin/bash

REGISTRY="http://localhost:8080"

docker exec -i beacon-network_db_registry_1 psql -U user -d registry \
    -c "INSERT INTO api_keys VALUES ('07b4e8ed58a6f97897b03843474c8cc981d154ffe45b10ef88a9f127b15c5c56', 'test key');"


curl -X 'POST' \
    "${REGISTRY}/services" \
    -H 'Authorization: 07b4e8ed58a6f97897b03843474c8cc981d154ffe45b10ef88a9f127b15c5c56' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "type": "beacon",
    "url": "https://staging-elixirbeacon.rahtiapp.fi"
    }'

curl -X 'POST' \
    "${REGISTRY}/services" \
    -H 'Authorization: 07b4e8ed58a6f97897b03843474c8cc981d154ffe45b10ef88a9f127b15c5c56' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "type": "beacon-aggregator",
    "url": "http://app_aggregator:5050/service-info"
    }'
