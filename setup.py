from setuptools import setup

setup(
    name="beacon_network",
    version="1.6.6",
    description="Beacon Network services",
    long_description_content_type="text/markdown",
    project_urls={
        "Source": "https://github.com/CSCfi/beacon-network",
    },
    author="CSC - IT Center for Science",
    classifiers=[
        "Development Status :: 3 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.8",
    ],
    packages=[
        "aggregator",
        "aggregator/config",
        "aggregator/endpoints",
        "aggregator/utils",
        "registry",
        "registry/config",
        "registry/endpoints",
        "registry/schemas",
        "registry/utils",
    ],
    package_data={"": ["*.json", "*.ini"]},
    install_requires=[
        "asyncio==3.4.3",
        "aiohttp==3.8.6",
        "aiohttp-cors==0.7.0",
        "aiocache==0.12.2",
        "aiomcache==0.8.1",
        "ujson==5.8.0",
        "uvloop==0.14.0; python_version < '3.7'",
        "uvloop==0.17.0; python_version >= '3.7'",
        "asyncpg==0.28.0",
        "jsonschema==4.19.1",
        "gunicorn==21.2.0",
    ],
    extras_require={
        "test": [
            "coverage==7.3.1",
            "pytest<7.5",
            "pytest-cov==4.1.0",
            "testfixtures==7.2.0",
            "tox==4.11.3",
            "flake8==6.1.0",
            "flake8-docstrings==1.7.0",
            "asynctest==0.13.0",
            "aioresponses==0.7.4",
            "black==23.9.1",
        ],
        "docs": ["sphinx >= 1.4", "sphinx_rtd_theme==1.3.0"],
    },
    entry_points={
        "console_scripts": [
            "beacon_registry=registry.registry:main",
            "beacon_aggregator=aggregator.aggregator:main",
        ],
    },
)
