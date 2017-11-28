import asyncio
import json

from aiokafka.consumer import AIOKafkaConsumer
from aiokafka.producer import AIOKafkaProducer

from knockout_assignment.conf import settings


class FlightsTask:
    FLIGHTS_TOPIC = 'flights'
    PASSENGERS_AVERAGE_TOPIC = 'passengers_average'
    POPULATED_FLIGHT_TOPIC = 'populated_flight'

    def __init__(self):
        kafka_host = settings.kafka["default"]["BOOTSTRAP_SERVERS"]["HOST"]
        kafka_port = settings.kafka["default"]["BOOTSTRAP_SERVERS"]["PORT"]
        kafka_bootstrap_server = f'{kafka_host}:{kafka_port}'

        self.loop = asyncio.get_event_loop()
        self.consumer = AIOKafkaConsumer(self.FLIGHTS_TOPIC, loop=self.loop, value_deserializer=json.loads,
                                         group_id='flights_task', bootstrap_servers=kafka_bootstrap_server)
        self.producer = AIOKafkaProducer(loop=self.loop, value_serializer=lambda x: str(x).encode('utf-8'),
                                         bootstrap_servers=kafka_bootstrap_server)

    async def listen_flights(self):
        pass

    def run(self):
        self.loop.run_until_complete(self.listen_flights)
