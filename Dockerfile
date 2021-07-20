FROM python:3.9.6-alpine3.13 as BUILD

LABEL maintainer "CSC Developers"

RUN apk add --update \
    && apk add --no-cache build-base curl-dev linux-headers bash git \
    && apk add --no-cache libressl-dev libffi-dev \
    && apk add --no-cache supervisor \
    && rm -rf /var/cache/apk/*

RUN mkdir -p /app

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install .

FROM python:3.9.6-alpine3.13

RUN apk add --no-cache --update bash

LABEL maintainer "CSC Developers"
LABEL org.label-schema.schema-version="1.0"
LABEL org.label-schema.vcs-url="https://github.com/CSCFI/beacon-network"

COPY --from=BUILD /usr/local/lib/python3.8/ usr/local/lib/python3.8/

COPY --from=BUILD /usr/local/bin/gunicorn /usr/local/bin/

COPY --from=BUILD /usr/local/bin/beacon_registry /usr/local/bin/

COPY --from=BUILD /usr/local/bin/beacon_aggregator /usr/local/bin/

RUN mkdir -p /app

WORKDIR /app

COPY ./deploy/app.sh /app/app.sh

RUN chmod +x /app/app.sh

ENTRYPOINT ["/bin/sh", "-c", "/app/app.sh"]
