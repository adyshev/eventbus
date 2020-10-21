# -*- coding: utf-8 -*-
from abc import ABCMeta
from uuid import UUID, uuid4
from typing import Any, Dict, List, Type, Union, TypeVar, Optional
from decimal import Decimal

from eventbus.domain.decorators import subclassevents
from eventbus.domain.eventbus import AbstractEventBus
from eventbus.domain.events import (
    EventWithOriginatorID, CreatedEvent, AttributeChangedEvent,
    DomainEvent, EventWithTimestamp
)
from eventbus.domain.exceptions import OriginatorIDError
from eventbus.domain.whitehead import EnduringObject
from eventbus.util.topic import get_topic, resolve_topic


class MetaDomainEntity(ABCMeta):
    __subclassevents__ = False

    def __init__(cls, name: str, *args: Any, **kwargs: Any) -> None:  # noqa
        super().__init__(name, *args, **kwargs)
        if cls.__subclassevents__ is True:
            subclassevents(cls)


TDomainEntity = TypeVar("TDomainEntity", bound="DomainEntity")
TDomainEvent = TypeVar("TDomainEvent", bound="DomainEntity.Event")


class DomainEntity(EnduringObject, metaclass=MetaDomainEntity):
    """
    Supertype for domain model entity.
    """

    __subclassevents__ = False

    class Event(EventWithOriginatorID[TDomainEntity]):
        """
        Supertype for events of domain model entities.
        """

        def __check_obj__(self, obj: TDomainEntity) -> None:
            """
            Checks state of obj before mutating.

            :param obj: Domain entity to be checked.

            :raises OriginatorIDError: if the originator_id is mismatched
            """
            # Assert ID matches originator ID.
            if obj.id != self.originator_id:
                raise OriginatorIDError(
                    "'{0}' not equal to event originator ID '{1}'" "".format(obj.id, self.originator_id)
                )

    @classmethod
    async def __create__(
        cls: Type[TDomainEntity],
        event_bus: AbstractEventBus,
        originator_id: Optional[UUID] = None,
        event_class: Optional[Type["DomainEntity.Created[TDomainEntity]"]] = None,
        **kwargs: Any,
    ) -> TDomainEntity:
        """
        Creates a new domain entity.

        Constructs a "created" event, constructs the entity object
        from the event, publishes the "created" event, and returns
        the new domain entity object.

        :param cls DomainEntity: Class of domain event
        :param originator_id: ID of the new domain entity (defaults to ``uuid4()``).
        :param event_class: Domain event class to be used for the "created" event.
        :param kwargs: Other named attribute values of the "created" event.
        :return: New domain entity object.
        :rtype: DomainEntity
        """

        if originator_id is None:
            originator_id = uuid4()

        if event_class is None:
            created_event_class: Type[DomainEntity.Created[TDomainEntity]] = cls.Created
        else:
            created_event_class = event_class

        event = created_event_class(
            event_bus=event_bus, originator_id=originator_id, originator_topic=get_topic(cls), **kwargs
        )

        obj = event.__mutate__(None)

        if obj is None:
            raise ValueError("{0} returned None".format(type(event).__mutate__.__qualname__))

        await obj.__publish__(event)
        return obj

    class Created(CreatedEvent[TDomainEntity], Event[TDomainEntity]):
        """
        Triggered when an entity is created.
        """

        def __init__(self, event_bus: AbstractEventBus, originator_topic: str, **kwargs: Any):
            super(DomainEntity.Created, self).__init__(
                event_bus=event_bus, originator_topic=originator_topic, **kwargs
            )

        @property
        def originator_topic(self) -> str:
            """
            Topic (a string) representing the class of the originating domain entity.

            :rtype: str
            """
            return self.__dict__["originator_topic"]

        def __mutate__(self, obj: Optional[TDomainEntity]) -> Optional[TDomainEntity]:
            """
            Constructs object from an entity class,
            which is obtained by resolving the originator topic,
            unless it is given as method argument ``entity_class``.

            entity_class: Class of domain entity to be constructed.
            """
            entity_class: Type[TDomainEntity] = resolve_topic(self.originator_topic)
            return entity_class(**self.__entity_kwargs__)

        @property
        def __entity_kwargs__(self) -> Dict[str, Any]:
            kwargs = self.__dict__.copy()
            kwargs["event_bus"] = kwargs.pop("event_bus")
            kwargs["id"] = kwargs.pop("originator_id")
            kwargs.pop("originator_topic", None)
            kwargs.pop("__event_topic__", None)
            return kwargs

    def __init__(self, event_bus: AbstractEventBus, id: UUID, **kwargs):
        super().__init__()
        self._event_bus = event_bus
        self._id = id

    @property
    def id(self) -> UUID:
        """The immutable ID of the domain entity.

        This value is set using the ``originator_id`` of the
        "created" event constructed by ``__create__()``.

        An entity ID allows an instance to be
        referenced and distinguished from others, even
        though its state may change over time.

        This attribute has the normal "public" format for a Python object
        attribute name, because by definition all domain entities have an ID.
        """
        return self._id

    @property
    def event_bus(self) -> AbstractEventBus:
        return self._event_bus

    async def __change_attribute__(self: TDomainEntity, name: str, value: Any, **kwargs) -> None:
        """
        Changes named attribute with the given value,
        by triggering an AttributeChanged event.
        """
        event_class: Type["DomainEntity.AttributeChanged[TDomainEntity]"] = self.AttributeChanged
        await self.__trigger_event__(event_class=event_class, name=name, value=value, **kwargs)

    class AttributeChanged(Event[TDomainEntity], AttributeChangedEvent[TDomainEntity]):
        """
        Triggered when a named attribute is assigned a new value.
        """

        def __mutate__(self, obj: Optional[TDomainEntity]) -> Optional[TDomainEntity]:
            obj = super(DomainEntity.AttributeChanged, self).__mutate__(obj)
            setattr(obj, self.name, self.value)
            return obj

    async def __trigger_event__(self, event_class: Type[TDomainEvent], **kwargs: Any) -> None:
        """
        Constructs, applies, and publishes a domain event.
        """
        event: TDomainEvent = event_class(originator_id=self.id, **kwargs)
        self.__mutate__(event)
        await self.__publish__(event)

    def __mutate__(self, event: TDomainEvent) -> None:
        """
        Mutates this entity with the given event.

        This method calls on the event object to mutate this
        entity, because the mutation behaviour of different types
        of events was usefully factored onto the event classes, and
        the event mutate() method is the most convenient way to
        defined behaviour in domain models.

        However, as an alternative to implementing the mutate()
        method on domain model events, this method can be extended
        with a method that is capable of mutating an entity for all
        the domain event classes introduced by the entity class.

        Similarly, this method can be overridden entirely in subclasses,
        so long as all of the mutation behaviour is implemented in the
        mutator function, including the mutation behaviour of the events
        defined on the library event classes that would no longer be invoked.

        However, if the entity class defines a mutator function, or if a
        separate mutator function is used, then it must be involved in
        the event sourced repository used to replay events, which by default
        knows nothing about the domain entity class. In practice, this
        means having a repository for each kind of entity, rather than
        the application just having one repository, with each repository
        having a mutator function that can project the entity events
        into an entity.
        """
        if not isinstance(event, DomainEntity.Event):
            raise ValueError("Given Event is not an instance of DomainEntity.Event")

        event.__mutate__(self)

    async def __publish__(self, events: Union[TDomainEvent, List[TDomainEvent]]) -> None:
        """
        Publishes given event for subscribers in the application.

        :param events: domain event or list of events
        """
        if isinstance(events, DomainEvent):
            events = [events]

        await self._event_bus.publish(events)

    def __eq__(self, other: object) -> bool:
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)


TTimestampedEntity = TypeVar("TTimestampedEntity", bound="TimestampedEntity")


class TimestampedEntity(DomainEntity):
    def __init__(self, __created_on__: Decimal, **kwargs: Any):
        super(TimestampedEntity, self).__init__(**kwargs)
        self.___created_on__ = __created_on__
        self.___last_modified__ = __created_on__

    @property
    def __created_on__(self) -> Decimal:
        return self.___created_on__

    @property
    def __last_modified__(self) -> Decimal:
        return self.___last_modified__

    class Event(DomainEntity.Event[TTimestampedEntity], EventWithTimestamp[TTimestampedEntity]):
        """Supertype for events of timestamped entities."""

        def __mutate__(self, obj: Optional[TTimestampedEntity]) -> Optional[TTimestampedEntity]:
            """Updates 'obj' with values from self."""
            obj = super(TimestampedEntity.Event, self).__mutate__(obj)
            if obj is not None:
                obj.___last_modified__ = self.timestamp
            return obj

    class Created(DomainEntity.Created[TTimestampedEntity], Event[TTimestampedEntity]):
        """Published when a TimestampedEntity is created."""

        @property
        def __entity_kwargs__(self) -> Dict[str, Any]:
            # Get super property.
            kwargs = super(TimestampedEntity.Created, self).__entity_kwargs__
            kwargs["__created_on__"] = kwargs.pop("timestamp")
            return kwargs

    class AttributeChanged(Event[TTimestampedEntity], DomainEntity.AttributeChanged[TTimestampedEntity]):
        """Published when a TimestampedEntity is changed."""
