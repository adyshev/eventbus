# -*- coding: utf-8 -*-
class EventSourcingError(Exception):
    """Base eventsourcing exception."""


class TopicResolutionError(EventSourcingError):
    """Raised when unable to resolve a topic to a Python class."""


class ConsistencyError(EventSourcingError):
    """Raised when applying an event stream to a versioned entity."""


class MismatchedOriginatorError(ConsistencyError):
    """Raised when applying an event to an inappropriate object."""


class OriginatorIDError(MismatchedOriginatorError):
    """Raised when applying an event to the wrong entity or aggregate."""


class OriginatorVersionError(MismatchedOriginatorError):
    """Raised when applying an event to the wrong version of an entity or aggregate."""


class DataIntegrityError(ValueError, EventSourcingError):
    """ Raised when a sequenced item is damaged (hash doesn't match data)"""


class EntityIsDiscarded(AssertionError):
    """Raised when access to a recently discarded entity object is attempted."""


class ProgrammingError(EventSourcingError):
    """Raised when programming errors are encountered."""


class EncoderTypeError(TypeError):
    pass
