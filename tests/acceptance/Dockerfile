FROM python:3.6-alpine
MAINTAINER PeRDy

ENV APP=knockout-assignment
ENV WORKDIR=/srv/apps/$APP/acceptance/

RUN apk update && apk add --update ca-certificates bash curl && rm -rf /var/cache/apk/*

RUN mkdir -p $WORKDIR
WORKDIR $WORKDIR

COPY manifest.json requirements.txt constraints.txt $WORKDIR/
RUN curl https://downloads.getgauge.io/stable | sh && \
    gauge install -d $WORKDIR && \
    python -m pip install --no-cache-dir -r $WORKDIR/requirements.txt -c $WORKDIR/constraints.txt

COPY . $WORKDIR

ENTRYPOINT ["./run"]
