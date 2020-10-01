# -*- coding: utf-8 -*-
import pytest

from eventbus.application.eventbus import EventBus
from eventbus.example.entity import Example


@pytest.mark.asyncio
async def test_example_entity():
    bus = EventBus()

    assert bus.assert_event_handlers_empty() is None

    received_events = []

    async def receive_events(events):
        received_events.extend(events)

    bus.subscribe(handler=receive_events)

    # "Example.Created" has been added to a pending list (Domain Root Entity)
    example = await Example.__create__(event_bus=bus, first_name="First", last_name="Last", age=56)

    assert len(example.__pending_events__) == 1
    assert len(received_events) == 0

    for value in [10, 20, 30]:
        # "ExampleInternal.Created" has been published (Domain Entity)
        # "Example.ExampleInternalAdded" bas been added to a pending list (Domain Root Entity)
        await example.add(value)

    # 3x "ExampleInternal.Created"
    assert len(received_events) == 3

    # 1x "Example.Created" + 3x "Example.ExampleInternalAdded"
    assert len(example.__pending_events__) == 4

    # 1x "Example.Created" has been published
    await example.__save__()

    assert example.summ == 60

    assert len(example.__pending_events__) == 0

    # 3x "ExampleInternal.Created" + 1x "Example.Created" + 3x "ExampleInternal.Created"
    assert len(received_events) == 7
