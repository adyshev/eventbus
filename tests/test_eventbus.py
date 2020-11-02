# -*- coding: utf-8 -*-
from datetime import datetime, timezone
import random
from typing import List, Optional, Union, Type, Tuple
from uuid import uuid4

import pytest

from eventbus.application.eventbus import subscribe
from eventbus.domain.eventbus import AbstractEventHandler
from eventbus.domain.events import DomainEvent
from eventbus.domain.exceptions import EntityIsDiscarded, OriginatorVersionError, OriginatorIDError
from eventbus.domain.whitehead import TEvent
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

    # Same instance of handler will be skipped
    subscribe(handler1)
    # No such events thus skipping as well
    subscribe(handler2)

    # "Example.Created" has been added to a pending list (Domain Root Entity)
    example = await Example.__create__(first_name="First", last_name="Last", age=56)
    assert example.__version__ == 0

    # All dates are in default state
    assert example.__created_on__ == example.__updated_on__ == example.__last_modified__

    assert len(example.__pending_events__) == 1
    assert len(received_events) == 0

    for value in [10, 20, 30]:
        # "ExampleInternal.Created" has been published (Domain Entity)
        # "Example.ExampleInternalAdded" bas been added to a pending list (Domain Root Entity)
        await example.add(value)

    assert example.__version__ == 3

    # __updated_on__ remains unchanged
    assert example.__last_modified__ > example.__created_on__
    assert example.__created_on__ == example.__updated_on__

    await example.__trigger_event__(Example.AttributeChanged, name="first_name", value="First 2")

    assert example.__version__ == 4

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

    # Instantiate entity with discarted state
    now = datetime.now(tz=timezone.utc)
    another_example = Example(
        id=uuid4(),
        first_name="First #2",
        last_name="Last #2",
        age=56,
        discarded=True,
        __version__=0,
        __created_on__=now,
        __updated_on__=now
    )

    # Rises EntityIsDiscarded if event sent for discarded entity
    with pytest.raises(EntityIsDiscarded):
        await another_example.__trigger_event__(Example.AttributeChanged, name="first_name", value="First #3")

    # Create entity with discarted state
    another_example = await Example.__create__(
        first_name="First #2",
        last_name="Last #2",
        age=56,
        discarded=True
    )

    # Discarded state cannot be set via __create__ method
    assert another_example.__is_discarded__ is False

    # Trying to mutate entity by ivent with invalid version
    assert another_example.__version__ == 0
    # originator_version - version of entity after mutation by this event (in this case valid value is 1)
    event = Example.Event(originator_id=another_example.id, originator_version=100)

    with pytest.raises(OriginatorVersionError):
        another_example.__mutate__(event)

    # Trying to apply event with invalid originator_id, valid value is another_example.id
    event = Example.Event(originator_id=uuid4(), originator_version=1)

    with pytest.raises(OriginatorIDError):
        another_example.__mutate__(event)
