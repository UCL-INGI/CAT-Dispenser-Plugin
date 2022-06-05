#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="inginious-dispenser-cat",
    version="1.0",
    description="Plugin to add cat task dispenser",
    packages=find_packages(),
    install_requires=["inginious>=0.8dev0"],
    tests_require=[],
    extras_require={},
    scripts=[],
    include_package_data=True,
    author="Matthieu Leclercq et Clement Linsmeau",
    author_email="inginious@info.ucl.ac.be",
    license="AGPL 3",
    url="https://github.com/maleclercq/CAT-Dispenser-Plugin"
)
