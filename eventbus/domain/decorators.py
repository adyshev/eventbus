# -*- coding: utf-8 -*-
from typing import Dict, Type

from eventbus.domain.events import DomainEvent


def subclassevents(cls: type) -> type:  # noqa
    """
    Decorator that avoids "boilerplate" subclassing of domain events.

    For example, with this decorator you can do this:

    .. code::

        @subclassevents
        class Example(AggregateRoot):
            class SomethingHappened(DomainEvent): pass

    rather than this:

    .. code::

        class Example(AggregateRoot):
            class Event(AggregateRoot.Event): pass
            class Created(Event, AggregateRoot.Created): pass
            class AttributeChanged(Event, AggregateRoot.AttributeChanged): pass
            class Discarded(Event, AggregateRoot.Discarded): pass
            class SomethingHappened(Event): pass

    You can apply this to a tree of domain event classes by defining
    the base class with attribute 'subclassevents = True'.
    """

    bases_event_attrs = []
    super_event_class_names = set()
    for base_cls in cls.__bases__:
        base_event_attrs: Dict[str, Type[DomainEvent]] = {}
        bases_event_attrs.append(base_event_attrs)
        for base_attr_name in dir(base_cls):
            base_attr = getattr(base_cls, base_attr_name)
            if isinstance(base_attr, type) and issubclass(base_attr, DomainEvent):
                base_event_attrs[base_attr_name] = base_attr
                if base_attr_name != "Event":
                    super_event_class_names.add(base_attr_name)

    # Define base Event subclass including super Event classes.
    if "Event" in cls.__dict__:
        event_event_subclass = cls.__dict__["Event"]
    else:
        base_event_classes = []
        for base_event_attrs in bases_event_attrs:
            try:
                event_cls = base_event_attrs["Event"]
            except KeyError:
                pass
            else:
                base_event_classes.append(event_cls)

        event_event_subclass = type(
            "Event", tuple(base_event_classes or [DomainEvent]), {"__qualname__": cls.__name__ + ".Event"},
        )
        event_event_subclass.__module__ = cls.__module__
        setattr(cls, "Event", event_event_subclass)  # noqa

    # Define subclasses for super event classes, including Event subclass as base.
    for super_event_class_name in super_event_class_names:

        base_event_classes = [event_event_subclass]
        if super_event_class_name in cls.__dict__:
            continue

        for base_event_attrs in bases_event_attrs:
            try:
                event_cls = base_event_attrs[super_event_class_name]
            except KeyError:
                pass
            else:
                base_event_classes.append(event_cls)
        event_subclass = type(
            super_event_class_name,
            tuple(base_event_classes),
            {"__qualname__": cls.__name__ + "." + super_event_class_name},
        )
        event_subclass.__module__ = cls.__module__
        setattr(cls, super_event_class_name, event_subclass)

    # Redefine event classes in cls.__dict__ that are not subclasses of Event.
    for cls_attr_name in cls.__dict__.keys():
        cls_attr = getattr(cls, cls_attr_name)
        if isinstance(cls_attr, type) and issubclass(cls_attr, DomainEvent):
            if not issubclass(cls_attr, event_event_subclass):
                try:
                    event_subclass = type(
                        cls_attr_name,
                        (cls_attr, event_event_subclass),
                        {
                            "__qualname__": cls_attr.__qualname__,
                            "__module__": cls_attr.__module__,
                            "__doc__": cls_attr.__doc__,
                        },
                    )
                except TypeError:
                    raise Exception(cls_attr_name, cls_attr, event_event_subclass)
                setattr(cls, cls_attr_name, event_subclass)

    return cls
