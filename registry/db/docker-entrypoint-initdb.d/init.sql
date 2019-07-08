CREATE TABLE IF NOT EXISTS services (
    id VARCHAR(256),
    name VARCHAR(256),
    type VARCHAR(32),
    description VARCHAR(1024),
    documentation_url VARCHAR(512),
    organization VARCHAR(64),
    contact_url VARCHAR(512),
    api_version VARCHAR(8),
    service_version VARCHAR(8),
    extension JSONB,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (id)
);

CREATE TABLE service_keys (
    service_id VARCHAR(64),
    service_key VARCHAR(128)
);

CREATE UNIQUE INDEX unique_service ON service_keys (service_id);

CREATE TABLE api_keys (
    api_key VARCHAR(64),
    comment VARCHAR(256)
);
