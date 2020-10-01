# -*- coding: utf-8 -*-
from typing import Dict, List, Tuple, Optional

from eventbus.domain.eventbus import AbstractEventBus, Predicate, Handler
from eventbus.domain.whitehead import TEvent


class EventHandlersNotEmptyError(Exception):
    pass


class EventBus(AbstractEventBus):
    def __init__(self):
        self._subscriptions: List[Tuple[Optional[Predicate], Handler]] = []

    def subscribe(self, handler: Handler, predicate: Optional[Predicate] = None) -> None:
        """
        Adds 'handler' to list of event handlers
        to be called if 'predicate' is satisfied.

        If predicate is None, the handler will
        be called whenever an event is published.

        :param callable handler: Will be called when an event is published.
        :param callable predicate: Conditions whether the handler will be called.
        """
        if (predicate, handler) not in self._subscriptions:
            self._subscriptions.append((predicate, handler))

    def unsubscribe(self, handler: Handler, predicate: Optional[Predicate] = None) -> None:
        """
        Removes 'handler' from list of event handlers
        to be called if 'predicate' is satisfied.

        :param callable handler: Previously subscribed handler.
        :param callable predicate: Previously subscribed predicate.
        """
        if (predicate, handler) in self._subscriptions:
            self._subscriptions.remove((predicate, handler))

    async def publish(self, events: List[TEvent]) -> None:
        """
        Published given 'event' by calling subscribed event
        handlers with the given 'event', except those with
        predicates that are not satisfied by the event.

        Handlers are called in the order they are subscribed.

        :param DomainEvent events: Domain event to be published.
        """
        # A cache of conditions means predicates aren't evaluated
        # more than once for each event.
        cache: Dict[Predicate, bool] = {}
        for predicate, handler in self._subscriptions[:]:
            if predicate is None:
                await handler(events)  # noqa
            else:
                cached_condition = cache.get(predicate)
                if cached_condition is None:
                    condition = predicate(events)
                    cache[predicate] = condition
                    if condition:
                        await handler(events)  # noqa
                elif cached_condition is True:
                    await handler(events)  # noqa
                else:
                    pass

    def assert_event_handlers_empty(self) -> None:
        """
        Raises EventHandlersNotEmptyError, unless
        there are no event handlers subscribed.
        """
        if len(self._subscriptions):
            msg = "subscriptions still exist: %s" % self._subscriptions
            raise EventHandlersNotEmptyError(msg)

    def clear_event_handlers(self) -> None:
        """
        Removes all previously subscribed event handlers.
        """
        self._subscriptions.clear()
