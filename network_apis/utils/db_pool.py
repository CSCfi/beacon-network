"""Database connection pool."""

import os
import asyncpg

DB_SCHEMA = os.environ.get('DB_SCHEMA', '')  # optional variable for special cases
DB_SCHEMA += '.' if DB_SCHEMA else ''


async def init_db_pool(host=None, port=None, user=None, passwd=None, db=None):
    """Create a connection pool.
    As we will have frequent requests to the database it is recommended to create a connection pool.
    """
    # Get database credentials from function params or env
    host = host if host else os.environ.get('DB_HOST', 'localhost')
    port = port if port else os.environ.get('DB_PORT', '5432')
    user = user if user else os.environ.get('DB_USER', 'user')
    passwd = passwd if passwd else os.environ.get('DB_PASS', 'pass')
    db = db if db else os.environ.get('DB_NAME', 'db')
    return await asyncpg.create_pool(host=host,
                                     port=port,
                                     user=user,
                                     password=passwd,
                                     database=db,
                                     # initializing with 0 connections allows the web server to
                                     # start and also continue to live
                                     min_size=0,
                                     # for now limiting the number of connections in the pool
                                     max_size=20,
                                     max_queries=50000,
                                     timeout=120,
                                     command_timeout=180,
                                     max_cached_statement_lifetime=0,
                                     max_inactive_connection_lifetime=180)
