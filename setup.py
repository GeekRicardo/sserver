import os
from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

version = os.environ["PACKAGE_VERSION"]

setup(
    name="dserver",
    version=version,
    packages=find_packages(),
    author="Geek Ricardo",
    author_email="GeekRicardozzZ@gmail.com",
    install_requires=requirements,
    package_data={"sserver": ["templates/*", "upload/favicon.ico"]},
)
