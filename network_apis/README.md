# Beacon Network APIs
### Prerequisites
* Python3.6+
* PostgreSQL 9.6+ (one per service)



#### Setting up a database
It is recommended to set up a containerised database for services in case of multiple services running in the same environment.

Database connection credentials for both the Registry and Aggregator services can be changed at the [configuration file](/network_apis/config/config.ini). Using the example values, to set up a database for the Registry service:
```
cd db
docker run -d -e POSTGRES_USER=reg_user -e POSTGRES_PASSWORD=reg_pass -e POSTGRES_DB=reg_db -v "$PWD"/docker-entrypoint-initdb.d/:/docker-entrypoint-initdb.d/ -p 5438:5432 postgres:9.6
```

Using the same command, but changing the port for the Aggregator service:
```
cd db
docker run -d -e POSTGRES_USER=agg_user -e POSTGRES_PASSWORD=agg_pass -e POSTGRES_DB=agg_db -v "$PWD"/docker-entrypoint-initdb.d/:/docker-entrypoint-initdb.d/ -p 5439:5432 postgres:9.6
```

Now Registry DB should be available at `localhost:5438` and Aggregator DB should be available at `localhost:5439`.

### Run
#### Run without installing
```
git clone https://github.com/CSCfi/beacon-network/
cd beacon-network/network_apis
pip install -r requirements.txt
python3 -m registry    # starts registry
python3 -m aggregator  # starts aggregator
```
#### Install and run
```
git clone https://github.com/CSCfi/beacon-network/
cd beacon-network/network_apis
pip install .
beacon_registry    # starts registry
beacon_aggregator  # starts aggregator
```
#### Containerised
To be done: container deploy script for both services.

### After set-up examples
<details><summary>View examples</summary>
Register a service, on this case, register self at Registry (host's own details).

```
curl -X POST \
  http://localhost:3000/services \
  -d '{
    "id": "org.ga4gh.registry",
    "name": "ELIXIR Beacon Registry",
    "serviceType": "GA4GHRegistry",
    "serviceUrl": "https://example.org/service",
    "open": true,
    "apiVersion": "0.1",
    "organization": {
        "id": "org.ga4gh",
        "name": "Global Alliance for Genomic Health",
        "description": "Enabling responsible genomic data sharing for the benefit of human health.",
        "address": "Netstreet 100, Internet, Webland",
        "welcomeUrl": "https://ga4gh.org/",
        "contactUrl": "https://ga4gh.org/contactus/",
        "logoUrl": "https://www.ga4gh.org/wp-content/themes/ga4gh-theme/gfx/GA-logo-footer.png",
        "info": {
            "agenda": "Global Health",
            "affiliation": "The World"
        }
    },
    "description": "Beacon Registry service for ELIXIR node",
    "version": "1.0.0",
    "publicKey": "string",
    "welcomeUrl": "https://example.org/home",
    "alternativeUrl": "https://example.org/internal"
}'

# RESPONSE:
Service has been registered. Service key for updating and deleting registration, keep it safe: {SECRET_KEY}
```
`POST /services` returns a service key that the registrar should keep safe for updating and deleting the service details.

Updating service details, in this case, changing service id and name. The service key should be given in the `Beacon-Service-Key` header.
```
curl -X PUT \
  http://localhost:3000/services/org.ga4gh.registry \
  -H 'Beacon-Service-Key: {SECRET_KEY}' \
  -d '{
    "id": "org.ga4gh.registry-new",
    "name": "ELIXIR Central Registry",
    "serviceType": "GA4GHRegistry",
    "serviceUrl": "https://example.org/service",
    "open": true,
    "apiVersion": "0.1",
    "organization": {
        "id": "org.ga4gh",
        "name": "Global Alliance for Genomic Health",
        "description": "Enabling responsible genomic data sharing for the benefit of human health.",
        "address": "Netstreet 100, Internet, Webland",
        "welcomeUrl": "https://ga4gh.org/",
        "contactUrl": "https://ga4gh.org/contactus/",
        "logoUrl": "https://www.ga4gh.org/wp-content/themes/ga4gh-theme/gfx/GA-logo-footer.png",
        "info": {
            "agenda": "Global Health",
            "affiliation": "The World"
        }
    },
    "description": "Beacon Registry service for ELIXIR node",
    "version": "1.0.0",
    "publicKey": "string",
    "welcomeUrl": "https://example.org/home",
    "alternativeUrl": "https://example.org/internal"
}'
```

Get Registry's information.
```
curl -X GET \
  http://localhost:3000/info \
```

Register a Beacon to the Beacon Aggregator
```
curl -X POST \
  http://localhost:3001/services \
  -d '{
    "id": "org.ga4gh.beacon",
    "name": "ELIXIR Beacon",
    "serviceType": "GA4GHBeacon",
    "serviceUrl": "https://example.org/service",
    "open": true,
    "apiVersion": "1.0.0",
    "organization": {
        "id": "org.ga4gh",
        "name": "Global Alliance for Genomic Health",
        "description": "Enabling responsible genomic data sharing for the benefit of human health.",
        "address": "Netstreet 100, Internet, Webland",
        "welcomeUrl": "https://ga4gh.org/",
        "contactUrl": "https://ga4gh.org/contactus/",
        "logoUrl": "https://www.ga4gh.org/wp-content/themes/ga4gh-theme/gfx/GA-logo-footer.png",
        "info": {
            "agenda": "Global Health",
            "affiliation": "The World"
        }
    },
    "description": "Beacon service for ELIXIR node",
    "version": "1.0.0",
    "publicKey": "string",
    "welcomeUrl": "https://example.org/home",
    "alternativeUrl": "https://example.org/internal"
}'
```

Get Aggregator's registered services information.
```
curl -X GET \
  http://localhost:3001/services \
```

Make a synchronous http query to Aggregator's registered services.
```
curl -X GET \
  'http://localhost:3001/query?assemblyId=GRCh38&referenceName=1&start=1000&referenceBases=A&alternateBases=T' \
```

Make an asynchronous websocket query to Aggregator's registered services (requires a websocket client).
```
curl -X GET \
  'http://localhost:3001/query?assemblyId=GRCh38&referenceName=1&start=1000&referenceBases=A&alternateBases=T' \
  -H 'Connection: Upgrade' \
  -H 'Upgrade: Websocket' \
```

An example websocket client is available at [dev/wsclient.py](dev/wsclient.py). Run websocket client with:
```
python wsclient.py
```

For more examples and endpoints see the [API Specification](https://editor.swagger.io/?url=https://gist.githubusercontent.com/teemukataja/b583bd9c6c57afa9a04024f070c79a5b/raw/1b1eef9a8a538fd64f713a6ab3e562b382381ccd/beacon-network-specification-0_1.yml).
</details>