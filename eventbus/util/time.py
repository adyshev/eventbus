# -*- coding: utf-8 -*-
import time
import datetime
from uuid import UUID
from typing import Union, Optional
from decimal import Decimal


def decimaltimestamp_from_uuid(value: UUID) -> Decimal:
    """
    Return a floating point unix timestamp from UUID value.

    :param value:
    :return: Unix timestamp in seconds, with microsecond precision.
    :rtype: Decimal
    """
    return decimaltimestamp(timestamp_long_from_uuid(value) / 1e7)


def timestamp_long_from_uuid(value: UUID) -> int:
    """
    Returns an integer value representing a unix timestamp in tenths of microseconds.

    :param value:
    :return: Unix timestamp integer in tenths of microseconds.
    :rtype: int
    """
    if isinstance(value, str):
        value = UUID(value)

    return value.time - 0x01B21DD213814000


def decimaltimestamp(t: Optional[float] = None) -> Decimal:
    """
    A UNIX timestamp as a Decimal object (exact number type).

    Returns current time when called without args, otherwise
    converts given floating point number ``t`` to a Decimal
    with 9 decimal places.

    :param t: Floating point UNIX timestamp ("seconds since epoch").
    :return: A Decimal with 6 decimal places, representing the
            given floating point or the value returned by time.time().
    :rtype: Decimal
    """
    t = time.time() if t is None else t
    return Decimal("{0:.6f}".format(t))


def datetime_from_timestamp(t: Union[Decimal, float]) -> datetime.datetime:
    """
    Returns naive UTC datetime from decimal UNIX
    timestamps such as time.time().

    :param t: timestamp, either Decimal or float
    :return: datetime.datetime object
    """
    return datetime.datetime.fromtimestamp(float(t), tz=datetime.timezone.utc)


def timestamp_from_datetime(d: datetime.datetime) -> Decimal:
    return Decimal("{0:.6f}".format(d.timestamp()))
