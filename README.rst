*******************
Knockout Assignment
*******************

:Version: 1.0.0
:Status: final
:Author: José Antonio Perdiguero

    Knockout assignment.

Getting started
===============

Requirements
------------
The service created for this assignment is based on Docker containers and Docker Compose to run it locally:

#. Install Docker following `official docs <https://docs.docker.com/engine/installation/>`_.

#. Install Docker Compose following `official docs <https://docs.docker.com/compose/install/>`_.

Install
-------
Clone this project.


Update and Run services
-----------------------
Once project is cloned, to update it:

#. (If running) Shut down containers::

    ./make.py down

#. Build images::

    ./make.py build

#. Spin up the containers::

    ./make.py up

Help
----
Make utilities has a self-describing help that can be queried using::

    ./make.py -h

Also, each make command has its own help, e.g::

    ./make.py down -h

Running CI steps locally
========================

Build
-----
#. (If running) Shut down containers::

    ./make.py down

#. Build images::

    ./make.py build --ci

#. Build acceptance tests image::

    ./make.py acceptance_tests --build

Code Analysis
-------------
::

    ./make.py prospector

Unit tests
----------
::

    ./make.py unit_tests

Acceptance tests
----------------

Run acceptance tests::

    ./make.py acceptance_tests

Connect to Kafka
================
Utilities to connect to a Kafka topic acting as a consumer or producer are provided within this application.

Consumer
--------
Check consumer help::

    ./make.py run kafka_consumer -h


Producer
--------
Check producer help::

    ./make.py run kafka_producer -h
