import io
import logging
import threading
import time
from collections import defaultdict
from datetime import datetime
from functools import partial
from typing import Any, Dict

import fastavro
import schedule
from aiokafka.consumer import AIOKafkaConsumer
from aiokafka.producer import AIOKafkaProducer

from flights_analyzer.conf import settings
from tasks.utils import get_event_loop, get_schema

logger = logging.getLogger(__name__)


def serialize(schema: 'avro.schema.Schema', item: Dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    fastavro.writer(buffer, schema, [item])
    return buffer.read()


def deserialize(schema: 'avro.schema.Schema', item: bytes) -> Dict[str, Any]:
    return next(fastavro.reader(item, reader_schema=schema))


class FlightsCache:
    """
    Cache for keeping a set of latest flights and passengers per origin country. Thread safe.
    """
    def __init__(self):
        """
        Cache for keeping a set of latest flights. Thread safe.
        """
        self.lock = threading.RLock()
        self._flights = []
        self._passengers = defaultdict(int)

    def add_flight(self, flight: Dict[str, Any]):
        """
        Add a new flight to the cache. Thread safe.

        :param flight: New flight.
        """
        with self.lock:
            self._flights.append(flight)
            self._passengers[flight['origin']] += flight['passengers']

    def pop_flights(self):
        """
        Clear current flights cache and returns the state. Thread safe.

        :return: Current set of flights.
        """
        with self.lock:
            flights = self._flights
            self._flights = []
            return flights

    def pop_passengers(self):
        """
        Clear passengers and returns it. Thread safe.

        :return: Current mapping of passengers per origin country.
        """
        with self.lock:
            passengers = self._passengers
            self._passengers = defaultdict(int)
            return passengers


class FlightsTask:
    FLIGHTS_TOPIC = 'flights'
    PASSENGERS_AVERAGE_TOPIC = 'passengers_average'
    TREND_ORIGIN_TOPIC = 'trend_origin'

    def __init__(self):
        self.kafka_bootstrap_servers = ','.join(
            [f'{server["HOST"]}:{server["PORT"]}' for server in settings.kafka['default']['BOOTSTRAP_SERVERS']])

        self.cache = FlightsCache()
        self.flights_schema = get_schema('flights.avpr', 'flights.analyzer.Flight')
        self.average_passengers_schema = get_schema('flights.avpr', 'flights.analyzer.AveragePassengers')
        self.trend_origin_schema = get_schema('flights.avpr', 'flights.analyzer.TrendOrigin')

    async def _listen_flights(self, consumer: 'AIOKafkaConsumer'):
        await consumer.start()
        try:
            async for flight in consumer:
                self.cache.add_flight(flight)
        except KeyboardInterrupt:
            pass
        finally:
            await consumer.stop()

    async def _send_average_passengers(self, producer: 'AIOKafkaProducer'):
        await producer.start()
        try:
            flights = self.cache.pop_flights()
            passengers_average = {
                'passengers': int(sum([f['passengers'] for f in flights]) / len(flights)),
                'timestamp': datetime.utcnow().timestamp()
            }
            await producer.send_and_wait(self.PASSENGERS_AVERAGE_TOPIC, passengers_average)
        finally:
            await producer.stop()

    async def _send_trend_origin(self, producer: 'AIOKafkaProducer'):
        await producer.start()
        try:
            passengers = self.cache.pop_passengers()
            trend_origin = {
                'origin': max(passengers, key=lambda x: passengers[x]),
                'timestamp': datetime.utcnow().timestamp()
            }
            await producer.send_and_wait(self.TREND_ORIGIN_TOPIC, trend_origin)
        except ValueError:
            logger.info("No flights registered")
        finally:
            await producer.stop()

    def listen_flights(self):
        loop = get_event_loop()
        consumer = AIOKafkaConsumer(self.FLIGHTS_TOPIC, loop=loop, group_id='flights_task',
                                    value_deserializer=partial(deserialize, schema=self.flights_schema),
                                    bootstrap_servers=self.kafka_bootstrap_servers)

        loop.run_until_complete(self._listen_flights(consumer))

    def send_average_passengers(self):
        loop = get_event_loop()
        producer = AIOKafkaProducer(loop=loop, value_serializer=partial(serialize, self.average_passengers_schema),
                                    bootstrap_servers=self.kafka_bootstrap_servers)

        loop.run_until_complete(self._send_average_passengers(producer))

    def send_trend_origin(self):
        loop = get_event_loop()
        producer = AIOKafkaProducer(loop=loop, value_serializer=partial(serialize, self.trend_origin_schema),
                                    bootstrap_servers=self.kafka_bootstrap_servers)

        loop.run_until_complete(self._send_trend_origin(producer))

    def run(self):
        threading.Thread(target=self.listen_flights).start()

        schedule.every().second.do(self.send_average_passengers)
        schedule.every().day.do(self.send_trend_origin)

        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Exiting")
        finally:
            schedule.run_pending()
