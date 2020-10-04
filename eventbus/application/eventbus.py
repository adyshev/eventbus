# -*- coding: utf-8 -*-
from typing import List, Optional

from eventbus.domain.eventbus import AbstractEventBus, AbstractEventHandler
from eventbus.domain.whitehead import TEvent


class EventBus(AbstractEventBus):
    def __init__(self, handlers: Optional[List[AbstractEventHandler]] = None):
        self._subscriptions: List[AbstractEventHandler] = handlers or []

    def subscribe(self, handler: AbstractEventHandler) -> None:
        if handler not in self._subscriptions:
            self._subscriptions.append(handler)

    def unsubscribe(self, handler: AbstractEventHandler) -> None:
        if handler in self._subscriptions:
            self._subscriptions.remove(handler)

    async def publish(self, events: List[TEvent]) -> None:
        for handler in self._subscriptions[:]:
            if handler.predicate(events):
                await handler.handler(events)

    def is_event_handlers_empty(self) -> bool:
        return len(self._subscriptions) == 0

    def clear_event_handlers(self) -> None:
        self._subscriptions.clear()
