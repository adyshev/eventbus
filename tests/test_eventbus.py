# -*- coding: utf-8 -*-
from time import sleep
from typing import List, Optional, Union, Type, Tuple
from uuid import uuid4

import pytest

from eventbus.application.eventbus import EventBus
from eventbus.domain.eventbus import AbstractEventHandler
from eventbus.domain.events import DomainEvent
from eventbus.domain.exceptions import EntityIsDiscarded
from eventbus.domain.whitehead import TEvent, T
from eventbus.example.entity import Example


@pytest.mark.asyncio
async def test_example_entity():
    received_events = []

    class SomeEvent(DomainEvent):
        pass

    class NonExistentEventsTestHandler(AbstractEventHandler):
        @property
        def event_type(self) -> Optional[Union[str, Type, Tuple]]:
            return SomeEvent

        async def handler(self, events: List[TEvent]):
            received_events.extend(events)

    class AllEventsTestHandler(AbstractEventHandler):
        @property
        def event_type(self) -> Union[str, Type, Tuple]:
            return self.ASTERISK

        async def handler(self, events: List[TEvent]):
            received_events.extend(events)

    handler1 = AllEventsTestHandler()
    handler2 = NonExistentEventsTestHandler()

    bus = EventBus(handlers=[
        handler1, handler2
    ])

    # Same instance of handler will be skipped
    bus.subscribe(handler1)
    # No such events thus skipping as well
    bus.subscribe(handler2)

    # "Example.Created" has been added to a pending list (Domain Root Entity)
    example = await Example.__create__(event_bus=bus, first_name="First", last_name="Last", age=56)

    # All dates are in default state
    assert example.__created_on__ == example.__updated_on__ == example.__last_modified__

    assert len(example.__pending_events__) == 1
    assert len(received_events) == 0

    for value in [10, 20, 30]:
        # "ExampleInternal.Created" has been published (Domain Entity)
        # "Example.ExampleInternalAdded" bas been added to a pending list (Domain Root Entity)
        await example.add(value)

    # __updated_on__ remains unchanged
    assert example.__last_modified__ > example.__created_on__
    assert example.__created_on__ == example.__updated_on__

    await example.__trigger_event__(Example.AttributeChanged, name="first_name", value="First 2")

    # Entity mutated immidiatelly
    assert example.summ == 60
    assert example.first_name == "First 2"

    # __updated_on__ was changed
    assert example.__last_modified__ == example.__updated_on__
    assert example.__updated_on__ > example.__created_on__

    # 1x "Example.Created" + 3x "Example.ExampleInternalAdded + 1x Example.AttributeChanged"
    assert len(example.__pending_events__) == 5

    await example.__save__()

    # 1x "Example.Created" + 3x "Example.ExampleInternalAdded + 1x Example.AttributeChanged"
    assert len(example.__pending_events__) == 0

    # 3x "ExampleInternal.Created" + 1x "Example.Created" + 3x "ExampleInternal.Created + 1x Example.AttributeChanged"
    assert len(received_events) == 8

    await example.__discard__()

    # Rises EntityIsDiscarded if event sent for discarded entity
    with pytest.raises(EntityIsDiscarded):
        await example.__trigger_event__(Example.AttributeChanged, name="first_name", value="First 2")

