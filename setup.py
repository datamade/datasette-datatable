from setuptools import setup
import os

VERSION = "0.1.1"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="datasette-datatables",
    description="Export Datasette records as DataTables",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    url="https://github.com/simonw/datasette-yaml",
    project_urls={
        "Issues": "https://github.com/simonw/datasette-yaml/issues",
        "CI": "https://github.com/simonw/datasette-yaml/actions",
        "Changelog": "https://github.com/simonw/datasette-yaml/releases",
    },
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["datasette_datatables"],
    entry_points={"datasette": ["datatable = datasette_datatables"]},
    install_requires=["datasette"],
    extras_require={"test": ["pytest", "pytest-asyncio", "httpx", "sqlite-utils"]},
    tests_require=["datasette-datatables[test]"],
)
