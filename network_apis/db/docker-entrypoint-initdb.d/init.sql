/* COMMON TABLES FOR AGGREGATOR AND REGISTRY */

CREATE TABLE IF NOT EXISTS organisations (
    id VARCHAR(64),
    name VARCHAR(256),
    description VARCHAR(1024),
    address VARCHAR(512),
    welcome_url VARCHAR(512),
    contact_url VARCHAR(512),
    logo_url VARCHAR(1024),
    info JSONB,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS services (
    id VARCHAR(64),
    name VARCHAR(256),
    service_type VARCHAR(32),
    api_version VARCHAR(8),
    service_url VARCHAR(512),
    host_org VARCHAR(64),
    description VARCHAR(1024),
    service_version VARCHAR(8),
    public_key VARCHAR(2048),
    open BOOLEAN,
    welcome_url VARCHAR(512),
    alt_url VARCHAR(512),
    create_datetime TIMESTAMP WITH TIME ZONE,
    update_datetime TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (id),
    FOREIGN KEY (host_org) REFERENCES organisations (id)
);

CREATE TABLE service_keys (
    service_id VARCHAR(64),
    service_key VARCHAR(128)
);

CREATE UNIQUE INDEX unique_service ON service_keys (service_id);

/* NOT IMPLEMENTED */

-- CREATE TABLE IF NOT EXISTS networks (
--     id VARCHAR(64),
--     name VARCHAR(256),
--     description VARCHAR(1024),
--     host_org VARCHAR(64),
--     PRIMARY KEY (id),
--     FOREIGN KEY (host_org) REFERENCES organisations (id)
-- );

-- CREATE TABLE IF NOT EXISTS network_services (
--     network_id VARCHAR(64),
--     service_id VARCHAR(64),
--     FOREIGN KEY (network_id) REFERENCES networks (id),
--     FOREIGN KEY (service_id) REFERENCES services (id)
-- );

-- CREATE UNIQUE INDEX duplicate_service_in_network ON network_services (network_id, service_id);
