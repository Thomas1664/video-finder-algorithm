import pytest
from src.database.db import Database


@pytest.fixture
def db() -> Database:
    database = Database(":memory:")
    return database
