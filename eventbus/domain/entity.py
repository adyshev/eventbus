# -*- coding: utf-8 -*-
from abc import ABCMeta
from datetime import datetime
from uuid import UUID, uuid4
from typing import Any, Dict, List, Type, Union, TypeVar, Optional

from eventbus.application.eventbus import publish
from eventbus.domain.decorators import subclassevents
from eventbus.domain.events import (
    EventWithOriginatorID, CreatedEvent, AttributeChangedEvent,
    DomainEvent, EventWithOriginatorVersion, EventWithTimestamp, DiscardedEvent
)
from eventbus.domain.exceptions import OriginatorIDError, EntityIsDiscarded, OriginatorVersionError
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
            originator_id=originator_id, originator_topic=get_topic(cls), **kwargs
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

        def __init__(self, originator_topic: str, **kwargs: Any):
            super(DomainEntity.Created, self).__init__(
                originator_topic=originator_topic, **kwargs
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
            kwargs["id"] = kwargs.pop("originator_id")
            kwargs.pop("discarded", None)
            kwargs.pop("originator_topic", None)
            kwargs.pop("__event_topic__", None)
            return kwargs

    def __init__(self, id: UUID, discarded: bool = False, **kwargs):
        super().__init__()
        self._id = id
        self.__is_discarded__ = discarded

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

    class AttributeChanged(Event[TDomainEntity], AttributeChangedEvent[TDomainEntity]):
        """
        Triggered when a named attribute is assigned a new value.
        """

        def __mutate__(self, obj: Optional[TDomainEntity]) -> Optional[TDomainEntity]:
            obj = super(DomainEntity.AttributeChanged, self).__mutate__(obj)
            setattr(obj, self.name, self.value)
            return obj

    async def __change_attribute__(self: TDomainEntity, name: str, value: Any, **kwargs) -> None:
        """
        Changes named attribute with the given value,
        by triggering an AttributeChanged event.
        """
        event_class: Type["DomainEntity.AttributeChanged[TDomainEntity]"] = self.AttributeChanged
        await self.__trigger_event__(event_class=event_class, name=name, value=value, **kwargs)

    class Discarded(DiscardedEvent[TDomainEntity], Event[TDomainEntity]):
        """
        Triggered when a DomainEntity is discarded.
        """

        def __mutate__(self, obj: Optional[TDomainEntity]) -> Optional[TDomainEntity]:
            obj = super(DomainEntity.Discarded, self).__mutate__(obj)
            if obj is not None:
                obj.__is_discarded__ = True
            return None

    async def __discard__(self: TDomainEntity, **kwargs) -> None:
        """
        Discards self, by triggering a Discarded event.
        """
        event_class: Type["DomainEntity.Discarded[TDomainEntity]"] = self.Discarded
        await self.__trigger_event__(event_class=event_class, **kwargs)

    def __assert_not_discarded__(self) -> None:
        """
        Asserts that this entity has not been discarded.

        Raises EntityIsDiscarded exception if entity has been discarded already.
        """
        if self.__is_discarded__:
            raise EntityIsDiscarded("Entity is discarded")

    async def __trigger_event__(self, event_class: Type[TDomainEvent], **kwargs: Any) -> None:
        """
        Constructs, applies, and publishes a domain event.
        """
        self.__assert_not_discarded__()
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

        event.__check_obj__(self)
        event.__mutate__(self)

    async def __publish__(self, events: Union[TDomainEvent, List[TDomainEvent]]) -> None:
        """
        Publishes given event for subscribers in the application.

        :param events: domain event or list of events
        """
        if isinstance(events, DomainEvent):
            events = [events]

        await publish(events)

    def __eq__(self, other: object) -> bool:
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)


TVersionedEntity = TypeVar("TVersionedEntity", bound="VersionedEntity")
TVersionedEvent = TypeVar("TVersionedEvent", bound="VersionedEntity.Event")


class VersionedEntity(DomainEntity):
    def __init__(self, __version__: int, **kwargs: Any):
        super().__init__(**kwargs)
        self.___version__: int = __version__

    @property
    def __version__(self) -> int:
        return self.___version__

    async def __trigger_event__(self, event_class: Type[TDomainEvent], **kwargs: Any) -> None:
        """
        Increments the version number when an event is triggered.

        The event carries the version number that the originator
        will have when the originator is mutated with this event.
        (The event's "originator" version isn't the version of the
        originator before the event was triggered, but represents
        the result of the work of incrementing the version, which
        is then set in the event as normal. The Created event has
        version 0, and a newly created instance is at version 0.
        The second event has originator version 1, and so will the
        originator when the second event has been applied.
        """
        # Do the work of incrementing the version number.
        next_version = self.__version__ + 1
        # Trigger an event with the result of this work.
        await super(VersionedEntity, self).__trigger_event__(
            event_class=event_class, originator_version=next_version, **kwargs
        )

    class Event(
        EventWithOriginatorVersion[TVersionedEntity], DomainEntity.Event[TVersionedEntity],
    ):
        """Supertype for events of versioned entities."""

        def __mutate__(self, obj: Optional[TVersionedEntity]) -> Optional[TVersionedEntity]:
            obj = super(VersionedEntity.Event, self).__mutate__(obj)

            if obj is not None:
                obj.___version__ = self.originator_version
            return obj

        def __check_obj__(self, obj: TVersionedEntity) -> None:
            """
            Extends superclass method by checking the event's
            originator version follows (1 +) this entity's version.
            """
            super(VersionedEntity.Event, self).__check_obj__(obj)
            # Assert the version sequence is correct.
            if self.originator_version != obj.__version__ + 1:
                raise OriginatorVersionError(
                    (
                        "Event takes entity to version {0}, "
                        "but entity is currently at version {1}. "
                        "Event type: '{2}', entity type: '{3}', entity ID: '{4}'"
                        "".format(
                            self.originator_version,
                            obj.__version__,
                            type(self).__name__,
                            type(obj).__name__,
                            obj._id,  # noqa
                        )
                    )
                )

    class Created(DomainEntity.Created[TVersionedEntity], Event[TVersionedEntity]):
        """Published when a VersionedEntity is created."""

        def __init__(self, originator_version: int = 0, *args: Any, **kwargs: Any):
            super(VersionedEntity.Created, self).__init__(originator_version=originator_version, *args, **kwargs)

        @property
        def __entity_kwargs__(self) -> Dict[str, Any]:
            # Get super property.
            kwargs = super(VersionedEntity.Created, self).__entity_kwargs__
            kwargs["__version__"] = kwargs.pop("originator_version")
            return kwargs

    class AttributeChanged(Event[TVersionedEntity], DomainEntity.AttributeChanged[TVersionedEntity]):
        """Published when a VersionedEntity is changed."""

    class Discarded(Event[TVersionedEntity], DomainEntity.Discarded[TVersionedEntity]):
        """Published when a VersionedEntity is discarded."""


TTimestampedEntity = TypeVar("TTimestampedEntity", bound="TimestampedEntity")


class TimestampedEntity(DomainEntity):
    def __init__(self, __created_on__: datetime, __updated_on__: datetime, **kwargs: Any):
        super(TimestampedEntity, self).__init__(**kwargs)
        self.___created_on__ = __created_on__
        self.___updated_on__ = __updated_on__
        self.___last_modified__ = __created_on__

    @property
    def __created_on__(self) -> datetime:
        return self.___created_on__

    @property
    def __updated_on__(self) -> datetime:
        return self.___updated_on__

    @property
    def __last_modified__(self) -> datetime:
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
            timestamp = kwargs.pop("timestamp")
            kwargs["__created_on__"] = timestamp
            kwargs["__updated_on__"] = timestamp
            return kwargs

    class AttributeChanged(
        Event[TTimestampedEntity], DomainEntity.AttributeChanged[TTimestampedEntity]
    ):
        """Published when a TimestampedEntity is changed."""

        def __mutate__(self, obj: Optional[TTimestampedEntity]) -> Optional[TTimestampedEntity]:
            """Updates 'obj' with values from self."""
            obj = super(TimestampedEntity.AttributeChanged, self).__mutate__(obj)
            if obj is not None:
                obj.___updated_on__ = self.timestamp
            return obj

    class Discarded(Event[TTimestampedEntity], DomainEntity.Discarded[TTimestampedEntity]):
        """Published when a TimestampedEntity is discarded."""


TTimestampedVersionedEntity = TypeVar("TTimestampedVersionedEntity", bound="TimestampedVersionedEntity")


class TimestampedVersionedEntity(TimestampedEntity, VersionedEntity):
    class Event(
        TimestampedEntity.Event[TTimestampedVersionedEntity],
        VersionedEntity.Event[TTimestampedVersionedEntity],
    ):
        """Supertype for events of timestamped, versioned entities."""

    class Created(
        TimestampedEntity.Created[TTimestampedVersionedEntity],
        VersionedEntity.Created,
        Event[TTimestampedVersionedEntity],
    ):
        """Published when a TimestampedVersionedEntity is created."""

    class AttributeChanged(
        Event[TTimestampedVersionedEntity],
        TimestampedEntity.AttributeChanged[TTimestampedVersionedEntity],
        VersionedEntity.AttributeChanged[TTimestampedVersionedEntity],
    ):
        """Published when a TimestampedVersionedEntity is created."""

    class Discarded(
        Event[TTimestampedVersionedEntity],
        TimestampedEntity.Discarded[TTimestampedVersionedEntity],
        VersionedEntity.Discarded[TTimestampedVersionedEntity],
    ):
        """Published when a TimestampedVersionedEntity is discarded."""
