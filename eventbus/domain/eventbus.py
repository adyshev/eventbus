# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import List, Callable, Optional, Coroutine

from eventbus.domain.whitehead import TEvent

Predicate = Callable[[List[TEvent]], bool]
Handler = Callable[[List[TEvent]], Coroutine]


class AbstractEventBus(ABC):
    @abstractmethod
    def subscribe(self, handler: Handler, predicate: Optional[Predicate] = None) -> None:
        pass

    @abstractmethod
    def unsubscribe(self, handler: Handler, predicate: Optional[Predicate] = None) -> None:
        pass

    @abstractmethod
    async def publish(self, events: List[TEvent]) -> None:
        pass
