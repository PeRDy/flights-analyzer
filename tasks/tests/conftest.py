"""Pytest conf module.
"""
from unittest.mock import MagicMock

import avro.protocol
import pytest


# Mocks
class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


class ConsumerMock(AsyncMock):
    async def __aiter__(self):
        for item in self.items:
            yield item


class ProducerMock(AsyncMock):
    pass


# Fixtures
@pytest.fixture
def flights_protocol() -> 'avro.protocol.Protocol':
    with open('schemas/flights.avpr') as f:
        protocol = avro.protocol.Parse(f.read())

    return protocol


@pytest.fixture
def flight_schema(flights_protocol: 'avro.protocol.Protocol') -> 'avro.schema.RecordSchema':
    return flights_protocol.type_map['knockout.assignment.Flight']


@pytest.fixture
def average_passengers_schema(flights_protocol: 'avro.protocol.Protocol') -> 'avro.schema.RecordSchema':
    return flights_protocol.type_map['knockout.assignment.AveragePassengers']


@pytest.fixture
def kafka_consumer() -> ConsumerMock:
    return ConsumerMock()


@pytest.fixture
def kafka_producer() -> ProducerMock:
    return ProducerMock()
