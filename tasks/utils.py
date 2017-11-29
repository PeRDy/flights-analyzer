"""Common utilities.
"""
import asyncio
import os

import avro.protocol

__all__ = ['get_event_loop', 'get_schema']


def get_event_loop() -> 'asyncio.BaseEventLoop':
    """
    Retrieves current thread's event loop, or create a new one and set it as default if it doesn't exists.

    :return: Event loop.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop


def get_schema(protocol: str, schema: str) -> 'avro.schema.Schema':
    """
    Parses specified Avro protocol file and retrieves an schema.

    :param protocol: Protocol file.
    :param schema: Schema name.
    :return: Avro Schema
    """
    from flights_analyzer.conf import settings

    protocol_path = os.path.join(settings.schemas_path, protocol)
    if not os.path.exists(protocol_path):
        raise ValueError(f'Protocol "{protocol}" does not exists')

    with open(protocol_path) as f:
        protocol = avro.protocol.Parse(f.read())

    try:
        return protocol.type_map[schema]
    except KeyError:
        raise ValueError(f'Schema "{schema}" not found in protocol')
