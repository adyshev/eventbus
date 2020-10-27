# -*- coding: utf-8 -*-
from datetime import datetime, timezone
from uuid import UUID
from typing import Any, Generic, Optional

from eventbus.domain.whitehead import ActualOccasion, TEntity
from eventbus.util.hashing import hash_object
from eventbus.util.topic import get_topic
from eventbus.util.transcoding import ObjectJSONEncoder


class DomainEvent(ActualOccasion, Generic[TEntity]):
    """
    Base class for domain model events.

    Implements methods to make instances read-only,
    comparable for equality in Python, and have
    recognisable representations.Custom
    To make domain events hashable, this class also
    implements a method to create a cryptographic hash
    of the state of the event.
    """

    __json_encoder__ = ObjectJSONEncoder(sort_keys=True)
    __notifiable__ = True

    def __init__(self, **kwargs: Any):
        """
        Initialises event attribute values directly from constructor kwargs.
        """
        super().__init__()
        self.__dict__.update(kwargs)

    def __repr__(self) -> str:
        """
        Creates a string representing the type and attribute values of the event.

        :rtype: str
        """
        sorted_items = tuple(sorted(self.__dict__.items()))
        args_strings = ("{0}={1!r}".format(*item) for item in sorted_items)
        args_string = ", ".join(args_strings)
        return "{0}({1})".format(self.__class__.__qualname__, args_string)

    def __mutate__(self, obj: Optional[TEntity]) -> Optional[TEntity]:
        """
        Updates 'obj' with values from 'self'.

        Calls the 'mutate()' method.

        Can be extended, but subclasses must call super
        and return an object to their caller.

        :param obj: object (normally a domain entity) to be mutated
        :return: mutated object
        """
        if obj is not None:
            self.mutate(obj)
        return obj

    def mutate(self, obj: TEntity) -> None:
        """
        Updates ("mutates") given 'obj'.

        Intended to be overridden by subclasses, as the most
        concise way of coding a default projection of the event
        (for example into the state of a domain entity).

        The advantage of implementing a default projection
        using this method rather than __mutate__ is that you
        don't need to call super or return a value.

        :param obj: domain entity to be mutated
        """

    def __setattr__(self, key: Any, value: Any) -> None:
        """
        Inhibits event attributes from being updated by assignment.
        """
        raise AttributeError("DomainEvent attributes are read-only")

    def __eq__(self, other: object) -> bool:
        """
        Tests for equality of two event objects.

        :rtype: bool
        """
        return isinstance(other, DomainEvent) and self.__hash__() == other.__hash__()

    def __ne__(self, other: object) -> bool:
        """
        Negates the equality test.

        :rtype: bool
        """
        return not (self == other)

    def __hash__(self) -> int:
        """
        Computes a Python integer hash for an event.

        Supports Python equality and inequality comparisons.

        :return: Python integer hash
        :rtype: int
        """
        attrs = self.__dict__.copy()

        # Involve the topic in the hash, so that different types
        # with same attribute values have different hash values.
        attrs["__event_topic__"] = get_topic(type(self))

        # Calculate the cryptographic hash of the event.
        sha256_hash = self.__hash_object__(attrs)

        # Return the Python hash of the cryptographic hash.
        return hash(sha256_hash)

    @classmethod
    def __hash_object__(cls, obj: dict) -> str:
        """
        Calculates SHA-256 hash of JSON encoded 'obj'.

        :param obj: Object to be hashed.
        :return: SHA-256 as hexadecimal string.
        :rtype: str
        """
        return hash_object(cls.__json_encoder__, obj)


class EventWithOriginatorID(DomainEvent[TEntity]):
    """
    For events that have an originator ID.
    """

    def __init__(self, originator_id: UUID, **kwargs: Any):
        super(EventWithOriginatorID, self).__init__(originator_id=originator_id, **kwargs)

    @property
    def originator_id(self) -> UUID:
        """
        Originator ID is the identity of the object
        that originated this event.

        :return: A UUID representing the identity of the originator.
        :rtype: UUID
        """
        return self.__dict__["originator_id"]


class EventWithTimestamp(DomainEvent[TEntity]):
    """
    For events that have a timestamp value.
    """

    def __init__(self, timestamp: Optional[datetime] = None, **kwargs: Any):
        kwargs["timestamp"] = timestamp or datetime.now(tz=timezone.utc)
        super(EventWithTimestamp, self).__init__(**kwargs)

    @property
    def timestamp(self) -> datetime:
        """
        A UNIX timestamp as a datetime object.
        """
        return self.__dict__["timestamp"]


class EventWithOriginatorVersion(DomainEvent[TEntity]):
    """
    For events that have an originator version number.
    """

    def __init__(self, originator_version: int, **kwargs: Any):
        if not isinstance(originator_version, int):
            raise TypeError("Version must be an integer: {0}".format(originator_version))
        super(EventWithOriginatorVersion, self).__init__(originator_version=originator_version, **kwargs)

    @property
    def originator_version(self) -> int:
        """
        Originator version is the version of the object
        that originated this event.

        :return: A integer representing the version of the originator.
        """
        return self.__dict__["originator_version"]


class CreatedEvent(DomainEvent[TEntity]):
    """
    Happens when something is created.
    """


class DiscardedEvent(DomainEvent[TEntity]):
    """
    Happens when something is discarded.
    """


class AttributeChangedEvent(DomainEvent[TEntity]):
    """
    Happens when the value of an attribute changes.
    """

    @property
    def name(self) -> str:
        return self.__dict__["name"]

    @property
    def value(self) -> Any:
        return self.__dict__["value"]
