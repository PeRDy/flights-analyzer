import asyncio
import io
import logging
import threading
import time
from collections import defaultdict
from datetime import datetime
from functools import partial
from typing import Any, Dict

import schedule
from aiokafka.consumer import AIOKafkaConsumer
from aiokafka.producer import AIOKafkaProducer
from avro.io import BinaryDecoder, BinaryEncoder, DatumReader, DatumWriter

from flights_analyzer.conf import settings
from tasks.utils import get_schema

logger = logging.getLogger(__name__)


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
    """
    Task that listen to a Kafka topic for flights info, stores it in a cache and analyzes it in two ways periodically.

    The two analysis consists of:
    * Every minute calculates the average number of passengers per flight.
    * Every day calculates the country where most passengers took a flight.

    The output of each analysis will be pushed to a different Kafka topic.

    The task is done using multithreading to make sure of the periodic tasks run when they have to, and using async to
    vastly improves performance using aiokafka lib.
    """
    FLIGHTS_TOPIC = 'flights'
    AVERAGE_PASSENGERS_TOPIC = 'average_passengers'
    TREND_ORIGIN_TOPIC = 'trend_origin'

    def __init__(self):
        """
        Task that listen to a Kafka topic for flights info, stores it in a cache and analyzes it in two ways
        periodically.
        """
        self.kafka_bootstrap_servers = ','.join(
            [f'{server["HOST"]}:{server["PORT"]}' for server in settings.kafka['default']['BOOTSTRAP_SERVERS']])

        self.cache = FlightsCache()
        self.flights_schema = get_schema('flights.avpr', 'flights.analyzer.Flight')
        self.average_passengers_schema = get_schema('flights.avpr', 'flights.analyzer.AveragePassengers')
        self.trend_origin_schema = get_schema('flights.avpr', 'flights.analyzer.TrendOrigin')

    @staticmethod
    def deserialize(item: bytes, schema: 'avro.schema.Schema') -> Dict[str, Any]:
        return DatumReader(schema).read(BinaryDecoder(io.BytesIO(item)))

    @staticmethod
    def serialize(item: Dict[str, Any], schema: 'avro.schema.Schema') -> bytes:
        buffer = io.BytesIO()
        DatumWriter(schema).write(item, BinaryEncoder(buffer))
        buffer.seek(0)
        return buffer.read()

    async def _listen_flights(self, consumer: 'AIOKafkaConsumer'):
        """
        Listen a Kafka topic to gather flight information and stores it in a cache.
        """
        await consumer.start()
        async for msg in consumer:
            flight = msg.value
            logger.info('Received info from flight number "%s"', flight['flightNumber'])
            self.cache.add_flight(flight)

    async def _send_average_passengers(self, producer: 'AIOKafkaProducer'):
        """
        Flight analyzer that calculates average number of passengers per flight and push this data into a kafka topic.
        """
        await producer.start()
        try:
            flights = self.cache.pop_flights()
            average_passengers = {
                'passengers': int(sum([f['passengers'] for f in flights]) / len(flights)),
                'timestamp': int(datetime.utcnow().timestamp())
            }
            await producer.send_and_wait(self.AVERAGE_PASSENGERS_TOPIC, average_passengers)
            logger.info('%d average passengers', average_passengers['passengers'])
        except ZeroDivisionError:
            logger.info("No flights registered")
        except:
            logger.exception('Cannot send average passengers')
        finally:
            await producer.stop()

    async def _send_trend_origin(self, producer: 'AIOKafkaProducer'):
        """
        Flight analyzer that calculates the country where most passengers took a flight and push this data into a kafka
        topic.
        """
        await producer.start()
        try:
            passengers = self.cache.pop_passengers()
            trend_origin = {
                'origin': max(passengers, key=lambda x: passengers[x]),
                'timestamp': int(datetime.utcnow().timestamp())
            }
            await producer.send_and_wait(self.TREND_ORIGIN_TOPIC, trend_origin)
            logger.info('Trend origin "%s" with %d passengers', trend_origin['origin'],
                        passengers[trend_origin['origin']])
        except ValueError:
            logger.info("No flights registered")
        except:
            logger.exception('Cannot send trend origin')
        finally:
            await producer.stop()

    def listen_flights(self, loop):
        """
        Listen a Kafka topic to gather flight information and stores it in a cache. Wrapper method to be used as a
        thread function.
        """
        consumer = AIOKafkaConsumer(self.FLIGHTS_TOPIC, loop=loop, group_id='flights_task',
                                    bootstrap_servers=self.kafka_bootstrap_servers,
                                    value_deserializer=partial(self.deserialize, schema=self.flights_schema))

        asyncio.run_coroutine_threadsafe(self._listen_flights(consumer), loop)

    def send_average_passengers(self, loop):
        """
        Flight analyzer that calculates average number of passengers per flight and push this data into a kafka topic.
        Wrapper method to be used as a thread function.
        """
        producer = AIOKafkaProducer(loop=loop, bootstrap_servers=self.kafka_bootstrap_servers,
                                    value_serializer=partial(self.serialize, schema=self.average_passengers_schema))

        asyncio.run_coroutine_threadsafe(self._send_average_passengers(producer), loop)

    def send_trend_origin(self, loop):
        """
        Flight analyzer that calculates the country where most passengers took a flight and push this data into a kafka
        topic. Wrapper method to be used as a thread function.
        """
        producer = AIOKafkaProducer(loop=loop, bootstrap_servers=self.kafka_bootstrap_servers,
                                    value_serializer=partial(self.serialize, schema=self.trend_origin_schema))

        asyncio.run_coroutine_threadsafe(self._send_trend_origin(producer), loop)

    @staticmethod
    def _start_worker(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def run(self):
        """
        Main method that essentially runs three threads:
        * A listener for gathering flights info.
        * Average passengers analyzer (each minute).
        * Trend country analyzer (each day).
        """
        loop = asyncio.new_event_loop()

        # Worker thread
        threading.Thread(target=self._start_worker, args=(loop,)).start()

        # Listener
        threading.Thread(target=self.listen_flights, args=(loop,)).start()

        # Passengers analyzer
        schedule.every().minute.do(self.send_average_passengers, loop)

        # Trend origin analyzer
        schedule.every().minute.do(self.send_trend_origin, loop)
        # It's intended modified to run every minute, to create a visible run flow, as well as test it.
        # The real code is:
        # schedule.every().day.do(self.send_trend_origin)

        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Exiting")
            loop.stop()
