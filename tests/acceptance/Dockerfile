FROM python:3.6-alpine
MAINTAINER PeRDy

ENV APP=flights-analyzer
ENV WORKDIR=/srv/apps/$APP/acceptance/

RUN apk update && apk add --update ca-certificates bash curl && rm -rf /var/cache/apk/*

RUN mkdir -p $WORKDIR
WORKDIR $WORKDIR

COPY manifest.json requirements.txt constraints.txt $WORKDIR/
RUN curl -SsL https://downloads.getgauge.io/stable | sh && gauge install -d $WORKDIR
RUN python -m pip install --no-cache-dir -r requirements.txt -c constraints.txt && \
    rm -rf $HOME/.cache/pip/*

RUN apk update && apk del ca-certificates curl && rm -rf /var/cache/apk/*

COPY . $WORKDIR

ENTRYPOINT ["./run"]
