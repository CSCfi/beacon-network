"""Mocked database operations used in many tests."""

import asyncio


class Transaction:
    """Class Transaction."""

    def __init__(self, *args, **kwargs):
        """Initialize class."""
        pass

    async def __aenter__(self):
        """Initialize class."""
        pass

    async def __aexit__(self, *args):
        """Initialize class."""
        pass


class Statement(Transaction):
    """Class Transaction."""

    def __init__(self, query, return_value=[], **kwargs):
        """Initialize class."""
        self.__dict__.update(kwargs)
        self.return_value = return_value
        pass

    async def fetch(self, *args, **kwargs):
        """Mimic fetch."""
        if self.return_value:
            return self.return_value
        else:
            return []


class Connection:
    """Class Connection."""

    def __init__(self, return_value=[], **kwargs):
        """Initialize class."""
        self.__dict__.update(kwargs)
        self.return_value = return_value
        pass

    # async def fetch(self, *args, **kwargs):
    #     """Mimic fetch."""
    #     return []

    async def execute(self, query, *args):
        """Mimic execute."""
        return []

    async def close(self):
        """Mimic close."""
        pass

    async def __aenter__(self):
        """Initialize class."""
        pass

    async def __aexit__(self, *args):
        """Initialize class."""
        pass

    @asyncio.coroutine
    def prepare(self, query):
        """Mimic prepare."""
        return Statement(query, return_value=self.return_value)

    def transaction(self, *args, **kwargs):
        """Mimic transaction."""
        return Transaction(*args, **kwargs)
