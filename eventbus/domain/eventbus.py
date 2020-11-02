# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import List, Tuple, Type, Union

from eventbus.domain.whitehead import TEvent


class AbstractEventHandler(ABC):
    ASTERISK = "*"

    @property
    @abstractmethod
    def event_type(self) -> Union[str, Type, Tuple]:
        pass

    def filter(self, events: List[TEvent]):
        # When self.event_type == self.ASTERISK -> return all available events
        return list(filter(lambda elm: self.event_type == self.ASTERISK or isinstance(elm, self.event_type), events))

    def predicate(self, events) -> bool:
        return len(self.filter(events)) > 0

    @abstractmethod
    async def handler(self, events: List[TEvent]):
        pass
