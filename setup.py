import os, sys
from setuptools import setup, find_packages

setup_args = {}

setup_args.update(dict(
    name='earthsim',
    version="0.1",
    packages = find_packages(),
))

if __name__=="__main__":
    setup(**setup_args)
