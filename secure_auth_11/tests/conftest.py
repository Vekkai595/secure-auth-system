import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app


class FakeRedis:
    def __init__(self):
        self.store = {}
        self.expiry = {}

    def incr(self, key):
        self.store[key] = int(self.store.get(key, 0)) + 1
        return self.store[key]

    def expire(self, key, seconds):
        self.expiry[key] = seconds

    def delete(self, key):
        self.store.pop(key, None)
        self.expiry.pop(key, None)


@pytest.fixture()
def db_session(tmp_path, monkeypatch):
    db_file = tmp_path / 'test.db'
    engine = create_engine(f'sqlite:///{db_file}', connect_args={'check_same_thread': False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    fake_redis = FakeRedis()
    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr('app.core.rate_limit._redis_client', fake_redis)
    monkeypatch.setattr('app.core.rate_limit.get_redis_client', lambda: fake_redis)
    yield TestingSessionLocal
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def client(db_session):
    with TestClient(app) as c:
        yield c
