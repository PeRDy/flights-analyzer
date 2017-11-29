FROM python:3.6-alpine
MAINTAINER PeRDy

ENV APP=flights-analyzer
ENV WORKDIR=/srv/apps/$APP/app
ENV LOGDIR=/srv/apps/$APP/logs
ENV PYTHONPATH='$PYTHONPATH:$WORKDIR'

# Create initial dirs
RUN mkdir -p $WORKDIR $LOGDIR
WORKDIR $WORKDIR

RUN apk update && apk add --update ca-certificates gcc musl-dev && rm -rf /var/cache/apk/*

# Install pip requirements
COPY requirements.txt requirements_test.txt constraints.txt $WORKDIR/
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt -c constraints.txt && \
    rm -rf $HOME/.cache/pip/*
RUN python -m pip install --no-cache-dir -r requirements_test.txt -c constraints.txt && \
    rm -rf $HOME/.cache/pip/*

RUN apk update && apk del ca-certificates curl gcc && rm -rf /var/cache/apk/*

# Copy application
COPY . $WORKDIR

ENTRYPOINT ["./run"]
