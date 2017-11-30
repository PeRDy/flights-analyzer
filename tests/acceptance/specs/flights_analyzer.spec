Flights Analyzer
================
Flights analyzer task listen a Kafka topic and processes each flight data that comes from it.

Calculate average passengers
----------------------------
Every minute the analyzer will calculate the average passengers per flight and stream it through a Kafka topic.

* Produce messages using schema "flights.analyzer.Flight" from protocol "flights.avpr" into Kafka topic "flights"
    | flightNumber | planeType | passengers | landedAt   | origin |
    |--------------|-----------|------------|------------|--------|
    | foo1         | SMALL     | 50         | 1511978026 | es     |
    | foo2         | BIG       | 100        | 1511978036 | us     |
    | foo3         | BIG       | 150        | 1511978039 | es     |
* Consume "1" messages using schema "flights.analyzer.AveragePassengers" from protocol "flights.avpr" from Kafka topic "average_passengers" with timeout "120" seconds
* Asserts messages contains
    | passengers |
    |------------|
    | 100        |


Calculate trend origins
-----------------------
Every day the analyzer will calculate the country from which more passengers have flighted and stream it through a Kafka topic.

* Produce messages using schema "flights.analyzer.Flight" from protocol "flights.avpr" into Kafka topic "flights"
    | flightNumber | planeType | passengers | landedAt   | origin |
    |--------------|-----------|------------|------------|--------|
    | foo1         | SMALL     | 50         | 1511978026 | es     |
    | foo2         | BIG       | 100        | 1511978036 | us     |
    | foo3         | BIG       | 150        | 1511978039 | es     |
* Consume "1" messages using schema "flights.analyzer.TrendOrigin" from protocol "flights.avpr" from Kafka topic "trend_origin" with timeout "120" seconds
* Asserts messages contains
    | origin |
    |--------|
    | es     |
