FROM python:3.6-alpine
MAINTAINER PeRDy

ENV APP=knockout-assignment
ENV WORKDIR=/srv/apps/$APP/app
ENV LOGDIR=/srv/apps/$APP/logs
ENV PYTHONPATH='$PYTHONPATH:$WORKDIR'

# Create initial dirs
RUN mkdir -p $WORKDIR $LOGDIR
WORKDIR $WORKDIR

# Install pip requirements
COPY requirements.txt requirements_test.txt constraints.txt $WORKDIR/
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt -r requirements_test.txt -c constraints.txt && \
    rm -rf $HOME/.cache/pip/*

# Copy application
COPY . $WORKDIR

ENTRYPOINT ["./run"]
