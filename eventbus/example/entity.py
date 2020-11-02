# -*- coding: utf-8 -*-
from typing import Any, List, Optional

from eventbus.domain.aggregate import BaseAggregateRoot
from eventbus.domain.entity import TimestampedVersionedEntity


class ExampleInternal(TimestampedVersionedEntity):
    def __init__(self, value: int, **kwargs: Any):
        super().__init__(**kwargs)
        self.value = value

    class Event(TimestampedVersionedEntity.Event):
        pass


class Example(BaseAggregateRoot):
    def __init__(
        self,
        first_name: str,
        last_name: str,
        age: int,
        internals: Optional[List[ExampleInternal]] = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.first_name = first_name
        self.last_name = last_name
        self.age = age
        self.internals: List[ExampleInternal] = internals or []

    @property
    def summ(self) -> int:
        return sum(internal.value for internal in self.internals)

    class Event(BaseAggregateRoot.Event):
        pass

    class ExampleInternalAdded(Event):
        internal: ExampleInternal

        def mutate(self, obj):
            obj.internals.append(self.internal)

    async def add(self, value: int):
        internal = await ExampleInternal.__create__(value=value)
        await self.__trigger_event__(Example.ExampleInternalAdded, internal=internal)
