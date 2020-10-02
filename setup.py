#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = ["python-dateutil>=2.8.1"]

setup_requirements = ["pytest-runner", ]

test_requirements = ["pytest>=3", ]

description = """
Domain Entity, Root Aggregate, Bus and Events extracted from the awesome johnbywater/eventsourcing library and
async support was added.

Main Package documentation is available on <http://eventsourcing.readthedocs.io/>.

Motivation: I don't like evensourcing conceptually, I don't want to have event store in my projects at all. Howewer,
I do like DDD concepts incl. Domain Entities, Aggregates and Domain Events and the way how they were
implemented by johnbywater. Also I would like to have async supported.
"""

setup(
    author="Alexander A. Dyshev",
    author_email="adyshev@gmail.com",
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description=description,
    long_description=readme + "\n\n" + history,
    keywords=[
        "async domain entity",
        "async event bus",
        "async aggregate root",
        "domain eventbus"
    ],
    install_requires=requirements,
    license="MIT license",
    include_package_data=True,
    name="domain-eventbus",
    packages=find_packages(include=["eventbus", "eventbus.*"], exclude=["docs"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/adyshev/eventbus",
    version="0.1.0",
    zip_safe=False,
)
