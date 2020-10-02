=====================================
Domain Entities, Root Aggregate, Events and Event Bus
=====================================


.. image:: https://img.shields.io/pypi/v/eventbus.svg
        :target: https://pypi.python.org/pypi/domain-eventbus

.. image:: https://img.shields.io/travis/adyshev/eventbus.svg
        :target: https://travis-ci.com/adyshev/eventbus

.. image:: https://readthedocs.org/projects/eventbus/badge/?version=latest
        :target: https://eventbus.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


.. image:: https://pyup.io/repos/github/adyshev/eventbus/shield.svg
     :target: https://pyup.io/repos/github/adyshev/eventbus/
     :alt: Updates


Domain Entity, Root Aggregate, Bus and Events extracted from the awesome johnbywater/eventsourcing library and
async support was added.

Main Package documentation is available on <http://eventsourcing.readthedocs.io/>.

Motivation: I don't like evensourcing conceptually, I don't want to have event store in my projects at all. Howewer,
I do like DDD concepts incl. Domain Entities, Aggregates and Domain Events and the way how they were
implemented by johnbywater. Also I would like to have async supported.

* Free software: MIT license
* Documentation: https://eventbus.readthedocs.io.

Features
--------

* async support
* store agnostic
