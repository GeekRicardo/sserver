import configparser
from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

def read_version():
    config = configparser.ConfigParser()
    config.read('.bumpversion.cfg')
    return config['bumpversion']['current_version']

setup(
    name="dserver",
    version="0.1.10",
    packages=find_packages(),
    author="Geek Ricardo",
    author_email="GeekRicardozzZ@gmail.com",
    install_requires=requirements,
    package_data={"sserver": ["templates/*", "upload/favicon.ico"]},
)
