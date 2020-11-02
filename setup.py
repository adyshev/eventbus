#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = ["python-dateutil>=2.8.1", ]

setup_requirements = ["pytest-runner", "pyyaml>=5.3.1", "argh>=0.26.2"]

test_requirements = ["pytest>=3", ]

long_description = """
Domain Entities, Root Aggregate, Events and EventBus with Async flavor.
(Based on awasome johnbywater/eventsourcing library)

`Package documentation is now available <https://eventbus.readthedocs.io/>`_.

`Please raise issues on GitHub <https://github.com/adyshev/eventbus/issues>`_.
"""

setup(
    description="Domain Entities, Root Aggregate, Events and EventBus with Async flavor",
    long_description=long_description,
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
    keywords=[
        "async domain entity",
        "domain events",
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
    version="0.1.19",
    zip_safe=False,
)
