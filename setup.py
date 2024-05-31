import os

from setuptools import setup

VERSION = "0.1.1"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="datasette-datatable",
    description="Export Datasette records as a DataTable",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Forest Gregg and Derek Eder",
    url="https://github.com/datamade/datasette-datatable",
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["datasette_datatable"],
    entry_points={"datasette": ["datatable = datasette_datatable"]},
    install_requires=["datasette>=1.0a13"],
    extras_require={"test": ["pytest", "pytest-asyncio", "httpx", "sqlite-utils"]},
    tests_require=["datasette-datatable[test]"],
)
