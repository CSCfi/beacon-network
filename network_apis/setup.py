from setuptools import setup

setup(
    name='beacon_network',
    version='0.1.dev',
    description='Beacon Network services',
    long_description_content_type='text/markdown',
    project_urls={
        'Source': 'https://github.com/CSCfi/beacon-network',
    },
    author='CSC - IT Center for Science',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Internet :: Proxy Servers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.6',
    ],
    packages=['.', 'config', 'endpoints', 'schemas', 'utils'],
    package_data={'': ['*.json']},
    install_requires=['aiohttp', 'asyncpg', 'aiohttp_cors', 'uvloop', 'asyncpg'],
    entry_points={
        'console_scripts': [
            'beacon_registry=registry:main',
            'beacon_aggregator=aggregator:main'
        ],
    },
)
