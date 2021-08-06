#!/bin/bash

OTHER_REGISTRY="http://localhost:8082"
REGISTRY="http://localhost:8083"

docker exec -i beacon-network_db_registry_1 psql -U user -d registry \
    -c "INSERT INTO api_keys VALUES ('07b4e8ed58a6f97897b03843474c8cc981d154ffe45b10ef88a9f127b15c5c56', 'test key');"

docker exec -i beacon-network_other_db_registry_1 psql -U user -d registry \
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
    "url": "http://app_aggregator:5054/service-info"
    }'


curl -X 'POST' \
    "${OTHER_REGISTRY}/services" \
    -H 'Authorization: 07b4e8ed58a6f97897b03843474c8cc981d154ffe45b10ef88a9f127b15c5c56' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "type": "beacon",
    "url": "https://beaconpy-elixirbeacon.rahtiapp.fi"
    }'

curl -X 'POST' \
    "${REGISTRY}/services" \
    -H 'Authorization: 07b4e8ed58a6f97897b03843474c8cc981d154ffe45b10ef88a9f127b15c5c56' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "type": "beacon-aggregator",
    "url": "http://other_aggregator:5051/service-info"
    }'

curl -X 'POST' \
    "${REGISTRY}/services" \
    -H 'Authorization: 07b4e8ed58a6f97897b03843474c8cc981d154ffe45b10ef88a9f127b15c5c56' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "type": "beacon",
    "url": "http://bad_beacon:5052/service-info"
    }'

curl -X 'POST' \
    "${REGISTRY}/services" \
    -H 'Authorization: 07b4e8ed58a6f97897b03843474c8cc981d154ffe45b10ef88a9f127b15c5c56' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "type": "beacon",
    "url": "http://localhost:5050/service-info"
    }'
