from pathlib import Path

from pytest import fixture

from biomcp import http_client


@fixture
def anyio_backend():
    return "asyncio"


class DummyCache:
    def __init__(self):
        self.store = {}

    def set(self, key, value, expire=None):
        self.store[key] = value

    def get(self, key, default=None):
        return self.store.get(key, default)

    @property
    def count(self):
        return len(self.store)

    def close(self):
        self.store.clear()


@fixture
def http_cache():
    cache = DummyCache()
    http_client._cache = cache
    yield cache
    cache.close()


@fixture
def data_dir():
    return Path(__file__).parent.parent / "data"
