=======
History
=======

0.1.3 (2020-10-01)
------------------

* First release on PyPI.

0.1.6 (2020-10-05)
------------------

* Introducing AbstractEventHandler

0.1.7 (2020-10-07)
------------------

* Cleanup: Docs, Labels

0.1.9 (2020-10-07)
------------------

* Cleanup: Docs, setup.py

0.1.10 (2020-10-09)
-------------------

* Cleanup: Docs, setup.py

0.1.11 (2020-10-09)
-------------------

* Added possibility to specify custom __last_modified__ during entity instantiation

0.1.12 (2020-10-21)
-------------------

* Removed versioning and discard functionality, we don't need them since we don't have event store/sourcing

0.1.13 (2020-10-21)
-------------------

* Revert 0.1.11, __last_modified__ reverted back to internal only value

0.1.14 (2020-10-22)
-------------------

* Time. Moved from Decimal to Datetime format

0.1.15 (2020-10-23)
-------------------

* Added __updated_on__ parameter to TimestampedEntity. Will be updated by each AttributeChanged event mutation

0.1.16 (2020-10-25)
-------------------

* Reverted Discard functionality from 0.1.12

0.1.17 (2020-10-25)
-------------------

* Adding possibility to set discarded state for entity instantiation (but not for creation)

0.1.18 (2020-10-27)
-------------------

* Reverted Versioning but not Upcasting

0.1.19 (2020-11-02)
-------------------

* Depricating EventBus/AbstractEventBus classes. Move events accumulator to global space.
