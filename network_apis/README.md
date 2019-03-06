# Beacon Network APIs
### Prerequisites
##### Minimal:
* Python3.6+
* PostgreSQL 9.6+

##### Recommended:
* Docker
* Docker Compose

### Automatic Setup
First build image and run both apps and databases simultaneously in their own networks. For reference, see [compose file](docker-compose.yml).
```
cd network_apis
docker build -t cscfi/beacon-network .
docker-compose up
```
By default, Registry will be available at `localhost:3000` and Aggregator at `localhost:3001` connected to their respective databases.

### Manual Setup
<details><summary>Setting up a database manually</summary>

#### Database
It is recommended to set up a containerised database for services in case of multiple services running in the same environment. But one can also set up local SQL databases.

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
</details>

<details><summary>Running web apps manually</summary>

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

#### Build containers and run
```
# Using s2i
cd network_apis
s2i build . centos/python-36-centos7 cscfi/beacon-network

# Or using docker
cd network_apis
docker build -t cscfi/beacon-network .

docker run -d -e BEACON_RUN_APP=registry cscfi/beacon-network      # starts registry
docker run -d -e BEACON_RUN_APP=aggregator cscfi/beacon-network    # starts aggregator
```

By default, Registry will be available at `localhost:3000` and Aggregator at `localhost:3001` connected to their respective databases.

</details>



### Environment Variables
Configuration priority is ENV > CONFIG > DEFAULT. Typically no ENV are set, so values are read from `config.ini`, which can be overridden with ENV.

<details><summary>Display table</summary>

| ENV            | Default                                    | Description                                                                                                                          |
|----------------|--------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| CONFIG_FILE    | `config.ini`                               | Location of configuration file, ablosute path.                                                                                       |
| BEACON_RUN_APP | ` `                                         | Specify which app to run inside a container. Possible values: `registry` and `aggregator`.                                           |
| DEBUG          | `False`                                    | Set to `True` to enable more debugging logs from functions.                                               |
| HTTPS_ONLY     | `False`                                    | Determine which HTTP schemas are allowed when contacting Beacons from an Aggregator. Set to `True` to enforce required HTTPS-schema. |
| HOST_ID        | ` `  | Unique service ID of this service, defaults to the value given in `config.ini`.                                                      |
| DB_HOST        | `localhost`  | Database address, defaults to value given in `config.ini` or `localhost`.                                                            |
| DB_PORT        | `5432`  | Database port, defaults to value given in `config.ini` or `5432`.                                                                    |
| DB_USER        | `user`  | Database user, defaults to value given in `config.ini` or `user`.                                                                    |
| DB_PASS        | `pass`  | Database password for user, defaults to value given in `config.ini` or `pass`.                                                       |
| DB_NAME        | `db`  | Database name, defaults to value given in `config.ini` or `db`.                                                                      |
| APP_HOST       | `0.0.0.0` | Web app service IP, defaults to value given in `config.ini` or `0.0.0.0`.                                                            |
| APP_PORT       | `8080` | Web app port, defaults to value given in `config.ini` or `8080`.                                                                     |

</details>

### After set-up examples
<details><summary>View examples</summary>

Register a service, on this case, register self at Registry (host's own details). Do the same for Aggregator, e.g. in testing/dev just change port from `3000` to `3001`. Aggregator will contact Registries that have been registered at its database.

```
curl -X POST \
  -H 'Post-Api-Key: {SECRET_KEY}' \
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
    "welcomeUrl": "https://example.org/home",
    "alternativeUrl": "https://example.org/internal"
}'
```

Get Registry's information.
```
curl -X GET \
  http://localhost:3000/info \
```

Register a Beacon to Registry
```
curl -X POST \
  -H 'Post-Api-Key: {SECRET_KEY}' \
  http://localhost:3000/services \
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
    "welcomeUrl": "https://example.org/home",
    "alternativeUrl": "https://example.org/internal"
}'
```

Get Aggregator's registered services information. This should return Registries that the Aggregator uses.
```
curl -X GET \
  http://localhost:3001/services \
```

Querying an Aggregator makes the Aggregator query a Registry for Beacon services, which are returned to the Aggregator for querying.

Make a synchronous http query to Aggregator's registered services.
```
curl -X GET \
  'http://localhost:3001/query?assemblyId=GRCh38&referenceName=1&start=1000&referenceBases=A&alternateBases=T' \
```

Make an asynchronous websocket query to Aggregator's registered services (requires a websocket client).
Websocket connection requires following headers: `Connection: Upgrade` and `Upgrade: Websocket`. Secure websocket `wss` protocol should always be used.

An example websocket client is available at [dev/wsclient.py](dev/wsclient.py). Run websocket client with:
```
python wsclient.py
```

Websocket connection can also be tested with a JS client, e.g. [snippet from Beacon UI](https://github.com/CSCfi/beacon-network/blob/master/ui/ui/view/view.js#L115-L144).

For more examples and endpoints see the [API Specification](https://editor.swagger.io/?url=https://gist.githubusercontent.com/teemukataja/b583bd9c6c57afa9a04024f070c79a5b/raw/1b1eef9a8a538fd64f713a6ab3e562b382381ccd/beacon-network-specification-0_1.yml).
</details>
