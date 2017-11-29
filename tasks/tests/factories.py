"""Factories to ease the creation of data for unit tests.
"""
import factory
import factory.fuzzy

__all__ = ['FlightFactory', 'AveragePassengersFactory', 'TrendOriginFactory']


class FlightFactory(factory.Factory):
    flightNumber = factory.Faker('md5')
    planeType = factory.fuzzy.FuzzyChoice(('SMALL', 'BIG'))
    passengers = factory.fuzzy.FuzzyInteger(1, 100)
    landedAt = factory.Faker('unix_time')
    origin = factory.Faker('country_code')


class AveragePassengersFactory(factory.Factory):
    passengers = factory.fuzzy.FuzzyInteger(1, 100)
    timestamp = factory.Faker('unix_time')


class TrendOriginFactory(factory.Factory):
    origin = factory.Faker('country_code')
    timestamp = factory.Faker('unix_time')
