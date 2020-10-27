# -*- coding: utf-8 -*-
class DomainEventError(Exception):
    """Base eventsourcing exception."""


class TopicResolutionError(DomainEventError):
    """Raised when unable to resolve a topic to a Python class."""


class ConsistencyError(DomainEventError):
    """Raised when applying an event stream to a versioned entity."""


class MismatchedOriginatorError(ConsistencyError):
    """Raised when applying an event to an inappropriate object."""


class OriginatorIDError(MismatchedOriginatorError):
    """Raised when applying an event to the wrong entity or aggregate."""


class OriginatorVersionError(MismatchedOriginatorError):
    """Raised when applying an event to the wrong version of an entity or aggregate."""


class EntityIsDiscarded(AssertionError):
    """Raised when access to a recently discarded entity object is attempted."""


class EncoderTypeError(TypeError):
    pass
