#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="inginious-dispenser-demo",
    version="0.1dev0",
    description="Plugin to add demo task dispenser",
    packages=find_packages(),
    install_requires=["inginious>=0.8dev0"],
    tests_require=[],
    extras_require={},
    scripts=[],
    include_package_data=True,
    author="The INGInious authors",
    author_email="inginious@info.ucl.ac.be",
    license="AGPL 3",
    url="https://github.com/UCL-INGI/INGInious-dispenser-demo"
)
