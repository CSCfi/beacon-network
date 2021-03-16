from setuptools import setup

setup(
    name='beacon_network',
    version='0.2.dev',
    description='Beacon Network services',
    long_description_content_type='text/markdown',
    project_urls={
        'Source': 'https://github.com/CSCfi/beacon-network',
    },
    author='CSC - IT Center for Science',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.6',
    ],
    packages=['aggregator', 'aggregator/config', 'aggregator/endpoints',
              'aggregator/utils', 'registry', 'registry/config',
              'registry/endpoints', 'registry/schemas',
              'registry/utils'],
    package_data={'': ['*.json', '*.ini']},
    install_requires=[
        'aiohttp', 'asyncpg', 'aiohttp_cors', 'uvloop',
        'asyncio', 'aiocache', 'aiomcache', 'ujson',
        'jsonschema==3.0.2', 'gunicorn'
    ],
    extras_require={
        'test': ['coverage', 'pytest<6.3', 'pytest-cov',
                 'coveralls', 'testfixtures', 'tox',
                 'flake8', 'flake8-docstrings', 'asynctest', 'aioresponses'],
        'docs': [
            'sphinx >= 1.4',
            'sphinx_rtd_theme']
    },
    entry_points={
        'console_scripts': [
            'beacon_registry=registry.registry:main',
            'beacon_aggregator=aggregator.aggregator:main'
        ],
    }
)
