"""Database connection pool."""

import asyncpg


async def init_db_pool(host, port, user, passwd, db):
    """Create a connection pool.

    As we will have frequent requests to the database it is recommended to create a connection pool.
    """
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
