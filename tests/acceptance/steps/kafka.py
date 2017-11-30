import asyncio
import io
import os
from functools import partial

import avro.protocol
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from avro.io import BinaryDecoder, BinaryEncoder, DatumReader, DatumWriter
from getgauge.python import DataStoreFactory, step


def get_schema(protocol, schema):
    protocol_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'schemas', protocol))
    if not os.path.exists(protocol_path):
        raise ValueError(f'Protocol "{protocol}" does not exists')

    with open(protocol_path) as f:
        protocol = avro.protocol.Parse(f.read())

    try:
        return protocol.type_map[schema]
    except KeyError:
        raise ValueError(f'Schema "{schema}" not found in protocol')


def serialize(item, schema):
    buffer = io.BytesIO()
    DatumWriter(schema).write(item, BinaryEncoder(buffer))
    buffer.seek(0)
    return buffer.read()


def deserialize(item, schema):
    return DatumReader(schema).read(BinaryDecoder(io.BytesIO(item)))


async def _produce_messages(producer, topic, messages):
    await producer.start()
    try:
        for message in messages:
            await producer.send_and_wait(topic, message)
    finally:
        await producer.stop()


async def _consume_messages(consumer, number_messages, timeout):
    await consumer.start()
    try:
        data = await consumer.getmany(max_records=number_messages, timeout_ms=timeout * 1000)
        messages = [m.value for _, ms in data.items() for m in ms]
    finally:
        await consumer.stop()

    return messages


@step("Create a Kafka producer with schema <schema> from protocol <protocol>")
def create_kafka_producer_with_schema(schema, protocol):
    avro_schema = get_schema(protocol, schema)
    producer = AIOKafkaProducer(loop=asyncio.get_event_loop(), value_serializer=partial(serialize, schema=avro_schema),
                                bootstrap_servers=os.environ['kafka_bootstrap_servers'])

    DataStoreFactory.scenario_data_store().put('producer', producer)


@step("Produce messages into topic <topic> <table>")
def produce_messages(topic, table):
    messages = [dict(zip(table.headers, [row[0], row[1], int(row[2]), int(row[3]), row[4]])) for row in table]
    producer = DataStoreFactory.scenario_data_store().get('producer')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_produce_messages(producer, topic, messages))


@step("Create a Kafka consumer with schema <schema> from protocol <protocol> listening to topic <topic>")
def create_kafka_consumer_with_schema_listening_to_topic(schema, protocol, topic):
    avro_schema = get_schema(protocol, schema)
    consumer = AIOKafkaConsumer(topic, loop=asyncio.get_event_loop(), group_id='acceptance_tests_group_id',
                                value_deserializer=partial(deserialize, schema=avro_schema),
                                bootstrap_servers=os.environ['kafka_bootstrap_servers'],
                                auto_offset_reset='earliest')

    DataStoreFactory.scenario_data_store().put('consumer', consumer)


@step("Consume <number_messages> messages with timeout <timeout>")
def consume_messages_with_timeout(number_messages, timeout):
    consumer = DataStoreFactory.scenario_data_store().get('consumer')
    loop = asyncio.get_event_loop()
    messages = loop.run_until_complete(_consume_messages(consumer, int(number_messages), int(timeout)))

    assert len(messages) == int(number_messages), f'{len(messages)} messages found, expected {int(number_messages)}'

    DataStoreFactory.scenario_data_store().put('messages', messages)


@step("Asserts messages contains <table>")
def asserts_messages_contains(table):
    message_asserts = [dict(zip(table.headers, row)) for row in table]
    messages = DataStoreFactory.scenario_data_store().get('messages')
    for message, asserts in zip(messages, message_asserts):
        for key, value in asserts.items():
            assert str(message[key]) == value, f'Value "{message[key]}" differs from expected "{value}"'
