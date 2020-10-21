# -*- coding: utf-8 -*-
class DomainEventError(Exception):
    """Base eventsourcing exception."""


class TopicResolutionError(DomainEventError):
    """Raised when unable to resolve a topic to a Python class."""


class OriginatorIDError(DomainEventError):
    """Raised when applying an event to the wrong entity or aggregate."""


class EncoderTypeError(TypeError):
    pass
