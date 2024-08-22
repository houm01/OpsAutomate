#!/usr/bin/env python
# coding: utf-8
from pathlib import Path
from setuptools import setup, find_packages


this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()


VERSION = '0.0.5'

setup(
    name='OpsAutomate',  # package name
    version=VERSION,  # package version
    description='ops automate',  # package description
    packages=find_packages(),
    url="https://github.com/houm01/OpsAutomate",
    zip_safe=False,
    long_description=long_description,
    long_description_content_type='text/markdown'
)