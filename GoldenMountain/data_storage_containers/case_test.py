"""Test cases for data_storage_containers."""

import pytest


class TestSQLiteContainer:
    """Tests for SQLiteContainer."""

    def test_store_and_load(self):
        from data_storage_containers import SQLiteContainer

        db = SQLiteContainer(path=":memory:")
        records = [{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}]
        db.store("users", records)

        result = db.load("users")
        assert len(result) == 2
        assert result[0]["name"] == "alice"
        db.close()

    def test_load_with_query(self):
        from data_storage_containers import SQLiteContainer

        db = SQLiteContainer(path=":memory:")
        db.store("users", [{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}])

        result = db.load("users", query={"id": 1})
        assert len(result) == 1
        assert result[0]["name"] == "alice"
        db.close()

    def test_update(self):
        from data_storage_containers import SQLiteContainer

        db = SQLiteContainer(path=":memory:")
        db.store("users", [{"id": 1, "name": "alice"}])

        count = db.update("users", query={"id": 1}, data={"name": "alice_updated"})
        assert count == 1
        assert db.load("users")[0]["name"] == "alice_updated"
        db.close()

    def test_delete(self):
        from data_storage_containers import SQLiteContainer

        db = SQLiteContainer(path=":memory:")
        db.store("users", [{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}])

        count = db.delete("users", query={"id": 1})
        assert count == 1
        assert len(db.load("users")) == 1
        db.close()

    def test_exists(self):
        from data_storage_containers import SQLiteContainer

        db = SQLiteContainer(path=":memory:")
        assert not db.exists("users")
        db.store("users", [{"id": 1}])
        assert db.exists("users")
        db.close()

    def test_store_empty_list(self):
        from data_storage_containers import SQLiteContainer

        db = SQLiteContainer(path=":memory:")
        db.store("users", [])
        assert not db.exists("users")
        db.close()


class TestContainerFactory:
    """Tests for ContainerFactory."""

    def test_create_sqlite(self):
        from data_storage_containers import ContainerFactory

        db = ContainerFactory.create("sqlite", path=":memory:")
        db.store("users", [{"id": 1}])
        assert db.exists("users")
        db.close()

    def test_create_unknown_raises(self):
        from data_storage_containers import ContainerFactory

        with pytest.raises(ValueError) as exc:
            ContainerFactory.create("unknown_type")
        assert "Unknown container" in str(exc.value)

    def test_available_containers(self):
        from data_storage_containers import ContainerFactory

        available = ContainerFactory.available()
        assert "sqlite" in available
        assert "postgres" in available
        assert "mongodb" in available
        assert "redis" in available


class TestContainerManager:
    """Tests for ContainerManager."""

    def test_add_default(self):
        from data_storage_containers import ContainerManager

        mgr = ContainerManager(default="sqlite")
        mgr.add(path=":memory:")
        mgr.store("users", [{"id": 1}])
        assert mgr.exists("users")
        mgr.close_all()

    def test_add_named(self):
        from data_storage_containers import ContainerManager

        mgr = ContainerManager()
        mgr.add("cache", container_type="sqlite", path=":memory:")
        mgr.get("cache").store("users", [{"id": 1}])
        assert mgr.get("cache").exists("users")
        mgr.close_all()

    def test_proxy_to_default(self):
        from data_storage_containers import ContainerManager

        mgr = ContainerManager(default="sqlite")
        mgr.add(path=":memory:")
        mgr.store("users", [{"id": 1, "name": "alice"}])

        result = mgr.load("users")
        assert len(result) == 1
        assert result[0]["name"] == "alice"
        mgr.close_all()

    def test_get_missing_raises(self):
        from data_storage_containers import ContainerManager

        mgr = ContainerManager()
        with pytest.raises(KeyError):
            mgr.get()

    def test_remove(self):
        from data_storage_containers import ContainerManager

        mgr = ContainerManager(default="sqlite")
        mgr.add(path=":memory:")
        mgr.store("users", [{"id": 1}])
        mgr.remove("sqlite")
        assert "sqlite" not in mgr.list_containers()

    def test_context_manager(self):
        from data_storage_containers import ContainerManager

        with ContainerManager(default="sqlite") as mgr:
            mgr.add(path=":memory:")
            mgr.store("users", [{"id": 1}])
            assert mgr.exists("users")
        # After exit, all closed


class TestRedisContainer:
    """Tests for RedisContainer (mock-based)."""

    def test_store_and_load(self):
        from data_storage_containers import RedisContainer

        db = RedisContainer(host="localhost")
        db._client = MockRedis()
        records = [{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}]
        db.store("users", records)

        result = db.load("users")
        assert len(result) == 2
        db.close()

    def test_store_with_ttl(self):
        from data_storage_containers import RedisContainer

        db = RedisContainer(host="localhost")
        db._client = MockRedis()
        db.store("cache", [{"key": "val"}], ttl=3600)
        assert db.exists("cache")
        db.close()


# Minimal mock for Redis
class MockRedis:
    def __init__(self):
        self._data = {}

    def delete(self, key):
        self._data.pop(key, None)

    def hset(self, key, field, value):
        if key not in self._data:
            self._data[key] = {}
        self._data[key][field] = value

    def hgetall(self, key):
        return self._data.get(key, {})

    def exists(self, key):
        return len(self._data.get(key, {})) > 0

    def expire(self, key, ttl):
        pass

    def close(self):
        pass
