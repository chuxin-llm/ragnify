
from setuptools import setup, find_packages

packages = find_packages()
requires = []

setup(
    name="llm-rag",
    version="1.0.0",
    fullname="llm-rag",
    description="",
    author="",
    author_email="",
    url="",
    platforms="",
    packages=packages,
    data_files=[],
    include_package_data=True,
    install_requires=requires,
    setup_requires=["wheel"],
    entry_points={
        "console_scripts": [
            "main = start:main"
        ]
    }
)