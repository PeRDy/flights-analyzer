*******************
Knockout Assignment
*******************

:Version: 1.0.0
:Status: final
:Author: José Antonio Perdiguero

    Flights analyzer.

Getting started
===============

Requirements
------------
The service created for this projecct is based on Docker containers and Docker Compose to run it locally:

#. Install Docker following `official docs <https://docs.docker.com/engine/installation/>`_.

#. Install Docker Compose following `official docs <https://docs.docker.com/compose/install/>`_.

Install
-------
Clone this project.


Update and Run services
-----------------------
Once project is cloned, to update it:

#. (If running) Shut down containers::

    ./make down

#. Build images::

    ./make build

#. Spin up the containers and let some seconds to everything start working::

    ./make up

#. Create a Kafka listener to *trend_origin* topic::

    ./make run kafka_consumer trend_origin flights.analyzer.TrendOrigin --bootstrap-servers=kafka:9092

#. Create a Kafka listener to *average_passengers* topic::

    ./make run kafka_consumer average_passengers flights.analyzer.AveragePassengers --bootstrap-servers=kafka:9092

#. Generate input::

    ./make run kafka_producer flights flights.analyzer.Flight --bootstrap-servers=kafka:9092 --file=data/es_500.json

Help
----
Make utilities has a self-describing help that can be queried using::

    ./make -h

Also, each make command has its own help, e.g::

    ./make down -h

Running CI steps locally
========================

Build
-----
#. (If running) Shut down containers::

    ./make down

#. Build images::

    ./make build --ci

#. Build acceptance tests image::

    ./make acceptance_tests --build

Code Analysis
-------------
::

    ./make prospector

Unit tests
----------
::

    ./make unit_tests

Acceptance tests
----------------
Shut down the stack (if running)::

    ./make down

Run acceptance tests::

    ./make acceptance_tests

Connect to Kafka
================
Utilities to connect to a Kafka topic acting as a consumer or producer are provided within this application.

Consumer
--------
Check consumer help::

    ./make run kafka_consumer -h


Producer
--------
Check producer help::

    ./make run kafka_producer -h

Assumptions
===========
* The language is not specified and I feel pretty comfortable with Python, so here it is.
* Since a script for loading input is requested, I created a command (as part of make file) that creates a Kafka consumer.
This script reads input from stdin, serialize it with Avro and pushes it into the Kafka topic. Also, instead of reading
from stdin, a jsonlines file can be specified, and the script will use it as the input.
* There is a counterpart of previous command for listening a Kafka topic and deserialize messages with Avro.
* Tests are necessary so I created some examples of unit tests and acceptance tests (using Gauge framework).
* I used the two letters version of ISO-3166.
* I increased the frequency of the task that calculates the country where most passengers took a flight to once per
minute, for testing and visibility purposes. Anyway, this is also commented in the code.

Considerations
==============
* I took advantage of some tools I previously developed, such as Clinner to create CLI.
* Chosen stack:
    * Python (3.6) as base language.
    * Kafka and Zookeeper as the streaming system.
    * Avro for data schemas system, providing (de)serialization based on predefined schemas.
    * Docker and Docker Compose for isolate services and raise the whole stack.
    * Unit testing is done with pytest and coverage.
    * Prospector used for lint.
    * Gauge as high level testing framework.
* I considered two possibles approach for this:
    * Creating two processes that listen the input topic (based on different cursors or offsets), process it, and
        generate the corresponding output.
    * Create three processes: one for listening the input topic, processing data and storing it in a buffer or cache; a
        second process that wakes up periodically, gets buffered data, process it and pushes the output into a topic.
* I chose the second approach to do the exercise a bit more realistic, having in mind that a common data processing is a
    typical use case. Obviously, this approach is harder to implement, because of the need of a caching system to
    communicate the data between the different processes.
* Knowing that it's a simple exercise and not a real-world service, I tried to replicate all the architecture needed
    using low level mechanisms such as concurrency, events, asynchronous tasks and in-memory cache; with the purpose of
    keeping it self-contained. This kind of services usually needs a proper architecture based on tasks and workers with
    high scalability factors, as well as a real cache like Redis.
