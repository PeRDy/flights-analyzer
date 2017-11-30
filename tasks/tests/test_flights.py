from datetime import datetime
from unittest.mock import call, patch, Mock

import factory
import pytest

from tasks.flights import FlightsTask
from tasks.tests.factories import FlightFactory, AveragePassengersFactory, TrendOriginFactory
from tasks.tests.conftest import kafka_producer, kafka_consumer


class TestFlightsTask:
    # Specific fixtures
    @pytest.fixture
    def flight_1(self):
        return factory.build(dict, passengers=130, origin='es', FACTORY_CLASS=FlightFactory)

    @pytest.fixture
    def flight_2(self):
        return factory.build(dict, passengers=170, origin='es', FACTORY_CLASS=FlightFactory)

    @pytest.fixture
    def flight_3(self):
        return factory.build(dict, passengers=200, origin='us', FACTORY_CLASS=FlightFactory)

    @pytest.fixture
    @pytest.mark.freeze_time('2017-11-28 06:00:00')
    def average_passengers(self):
        return factory.build(dict, passengers=150, timestamp=datetime.utcnow().timestamp(),
                             FACTORY_CLASS=AveragePassengersFactory)

    @pytest.fixture
    @pytest.mark.freeze_time('2017-11-28 06:00:00')
    def trend_origin(self):
        return factory.build(dict, origin='es', timestamp=datetime.utcnow().timestamp(),
                             FACTORY_CLASS=TrendOriginFactory)

    # Test cases
    @patch('tasks.flights.AIOKafkaProducer', new_callable=kafka_consumer)
    @pytest.mark.asyncio
    @pytest.mark.freeze_time('2017-11-28 06:00:00')
    async def test_listen_flights(self, mock_consumer, flight_1, flight_2, flight_3):
        mock_flight_1 = Mock()
        mock_flight_1.value = flight_1
        mock_flight_2 = Mock()
        mock_flight_2.value = flight_2
        mock_flight_3 = Mock()
        mock_flight_3.value = flight_3
        mock_consumer.items = [mock_flight_1, mock_flight_2, mock_flight_3]

        task = FlightsTask()

        await task._listen_flights(mock_consumer)

        assert task.cache._flights == [flight_1, flight_2, flight_3]
        assert task.cache._passengers == {'es': 300, 'us': 200}

    @patch('tasks.flights.AIOKafkaProducer', new_callable=kafka_producer)
    @pytest.mark.asyncio
    @pytest.mark.freeze_time('2017-11-28 06:00:00')
    async def test_calculate_average_passengers(self, mock_producer, flight_1, flight_2, average_passengers):
        expected_calls = [
            call(FlightsTask.AVERAGE_PASSENGERS_TOPIC, average_passengers),
        ]

        task = FlightsTask()
        task.cache._flights = [flight_1, flight_2]

        await task._send_average_passengers(mock_producer)

        assert mock_producer.send_and_wait.call_args_list == expected_calls

    @patch('tasks.flights.AIOKafkaProducer', new_callable=kafka_producer)
    @pytest.mark.asyncio
    @pytest.mark.freeze_time('2017-11-28 06:00:00')
    async def test_calculate_trend_origin(self, mock_producer, trend_origin):
        expected_calls = [
            call(FlightsTask.TREND_ORIGIN_TOPIC, trend_origin),
        ]

        task = FlightsTask()
        task.cache._passengers = {'es': 300, 'us': 200}

        await task._send_trend_origin(mock_producer)

        assert mock_producer.send_and_wait.call_args_list == expected_calls
