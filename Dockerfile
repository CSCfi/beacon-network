FROM python:3.8-alpine3.13

RUN apk add --update \
    && apk add --no-cache build-base curl-dev linux-headers bash git \
    && apk add --no-cache libressl-dev libffi-dev libstdc++ \
    && apk add --no-cache supervisor \
    && rm -rf /var/cache/apk/*

RUN mkdir -p /app/ui

WORKDIR /app

COPY requirements.txt .

# install the python requirements
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# copy the python directory structure
COPY aggregator /app/aggregator

# put the UI in place
COPY ui/dist /app/ui/dist

ENTRYPOINT ["python", "-m", "aggregator.aggregator"]
