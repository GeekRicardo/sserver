from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="dserver",
    version="0.1.0",
    packages=find_packages(),
    author="Geek Ricardo",
    author_email="GeekRicardozzZ@gmail.com",
    install_requires=requirements,
)
