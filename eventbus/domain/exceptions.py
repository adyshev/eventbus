# -*- coding: utf-8 -*-
class DomainEventError(Exception):
    """Base eventsourcing exception."""


class TopicResolutionError(DomainEventError):
    """Raised when unable to resolve a topic to a Python class."""


class OriginatorIDError(DomainEventError):
    """Raised when applying an event to the wrong entity or aggregate."""


class EntityIsDiscarded(AssertionError):
    """Raised when access to a recently discarded entity object is attempted."""


class EncoderTypeError(TypeError):
    pass
