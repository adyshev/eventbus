# -*- coding: utf-8 -*-
from typing import List

from eventbus.domain.eventbus import AbstractEventHandler
from eventbus.domain.whitehead import TEvent


_subscriptions: List[AbstractEventHandler] = []


def subscribe(handler: AbstractEventHandler) -> None:
    if handler not in _subscriptions:
        _subscriptions.append(handler)


def unsubscribe(handler: AbstractEventHandler) -> None:
    if handler in _subscriptions:
        _subscriptions.remove(handler)


async def publish(events: List[TEvent]) -> None:
    for handler in _subscriptions[:]:
        if handler.predicate(events):
            await handler.handler(events)


def is_event_handlers_empty() -> bool:
    return len(_subscriptions) == 0


def clear_event_handlers() -> None:
    _subscriptions.clear()
