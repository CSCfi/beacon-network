FROM python:3.8-alpine3.13

LABEL maintainer "CSC Developers"

RUN apk add --update \
    && apk add --no-cache build-base curl-dev linux-headers bash git \
    && apk add --no-cache libressl-dev libffi-dev \
    && apk add --no-cache supervisor \
    && rm -rf /var/cache/apk/*

RUN mkdir -p /app

WORKDIR /app

COPY . /app

RUN pip install .

ENTRYPOINT ["/bin/sh", "-c", "/app/deploy/app.sh"]
