FROM python:3.8-alpine3.13 as BUILD

LABEL maintainer="CSC Developers"

RUN apk add --update \
    && apk add --no-cache build-base curl-dev linux-headers bash git \
    && apk add --no-cache libressl-dev libffi-dev libstdc++ \
    && apk add --no-cache supervisor \
    && rm -rf /var/cache/apk/*

RUN mkdir -p /app

WORKDIR /app

COPY requirements.txt /app

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . /app

RUN pip install .

FROM node:18 as NODEBUILD

LABEL maintainer="CCI"

WORKDIR /app

COPY ui/ /app

RUN npm ci

RUN npm run build


FROM python:3.8-alpine3.13

RUN apk add --no-cache --update libstdc++

LABEL maintainer="CSC Developers"
LABEL org.label-schema.schema-version="1.0"
LABEL org.label-schema.vcs-url="https://github.com/CSCFI/beacon-network"

COPY --from=BUILD /usr/local/lib/python3.8/ usr/local/lib/python3.8/
COPY --from=BUILD /usr/local/bin/beacon_registry /usr/local/bin/
COPY --from=BUILD /usr/local/bin/beacon_aggregator /usr/local/bin/
# ok I (Patto) wouldn't have done it this way - but this is how the original code is bundled/dockerised
# so following suit - just copying the UI files into the site-packages (they are at ../ui/dist from the
# aggregator.py)
COPY --from=NODEBUILD /app/dist /usr/local/lib/python3.8/site-packages/ui/dist/

RUN mkdir -p /app

WORKDIR /app

ENTRYPOINT ["python", "-m", "aggregator.aggregator"]
