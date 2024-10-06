import pytest
import os
import json
from src.realtime_api_async_python.modules.memory_management import MemoryManager


@pytest.fixture
def temp_memory_file(tmp_path):
    memory_file = tmp_path / "test_memory.json"
    return str(memory_file)


@pytest.fixture
def memory_manager(temp_memory_file):
    return MemoryManager(temp_memory_file)


async def test_create(memory_manager):
    assert await memory_manager.create("test_key", "test_value")
    assert await memory_manager.read("test_key") == "test_value"
    assert not await memory_manager.create(
        "test_key", "new_value"
    )  # Should not create duplicate


async def test_read(memory_manager):
    await memory_manager.create("read_key", "read_value")
    assert await memory_manager.read("read_key") == "read_value"
    assert await memory_manager.read("non_existent_key") is None


async def test_update(memory_manager):
    await memory_manager.create("update_key", "original_value")
    assert await memory_manager.update("update_key", "updated_value")
    assert await memory_manager.read("update_key") == "updated_value"
    assert not await memory_manager.update(
        "non_existent_key", "value"
    )  # Should not update non-existent key


async def test_delete(memory_manager):
    await memory_manager.create("delete_key", "delete_value")
    assert await memory_manager.delete("delete_key")
    assert await memory_manager.read("delete_key") is None
    assert not await memory_manager.delete(
        "non_existent_key"
    )  # Should not delete non-existent key


async def test_list_keys(memory_manager):
    await memory_manager.create("key1", "value1")
    await memory_manager.create("key2", "value2")
    keys = await memory_manager.list_keys()
    assert "key1" in keys
    assert "key2" in keys
    assert len(keys) == 2


async def test_get_xml_for_prompt(memory_manager):
    await memory_manager.create("name", "John")
    await memory_manager.create("age", 30)
    await memory_manager.create("city", "New York")
    await memory_manager.create("file_1", "Content 1")
    await memory_manager.create("file_2", "Content 2")
    await memory_manager.create("data_something", "Some data")

    # Test exact match
    xml_string = await memory_manager.get_xml_for_prompt(
        ["name", "age", "non_existent"]
    )
    assert "<memory><name>John</name><age>30</age></memory>" in xml_string
    assert "non_existent" not in xml_string

    # Test for empty string when no keys match
    empty_string = await memory_manager.get_xml_for_prompt(
        ["non_existent_1", "non_existent_2"]
    )
    assert empty_string == ""

    # Test wildcard patterns
    all_match = await memory_manager.get_xml_for_prompt(["*"])
    assert all(
        key in all_match
        for key in ["name", "age", "city", "file_1", "file_2", "data_something"]
    )

    file_match = await memory_manager.get_xml_for_prompt(["file_*"])
    assert "<file_1>Content 1</file_1>" in file_match
    assert "<file_2>Content 2</file_2>" in file_match
    assert "name" not in file_match

    end_match = await memory_manager.get_xml_for_prompt(["*_something"])
    assert "<data_something>Some data</data_something>" in end_match
    assert "file_1" not in end_match

    mixed_match = await memory_manager.get_xml_for_prompt(
        ["name", "file_*", "*_something"]
    )
    assert all(
        item in mixed_match
        for item in [
            "<name>John</name>",
            "<file_1>Content 1</file_1>",
            "<file_2>Content 2</file_2>",
            "<data_something>Some data</data_something>",
        ]
    )
    assert "age" not in mixed_match


async def test_persistence(temp_memory_file):
    manager1 = MemoryManager(temp_memory_file)
    await manager1.create("persist_key", "persist_value")
    del manager1

    manager2 = MemoryManager(temp_memory_file)
    assert await manager2.read("persist_key") == "persist_value"


async def test_file_creation(temp_memory_file):
    await MemoryManager(temp_memory_file).load_memory()
    assert os.path.exists(temp_memory_file)


async def test_file_content(temp_memory_file):
    manager = MemoryManager(temp_memory_file)
    await manager.create("test_key", "test_value")

    with open(temp_memory_file, "r") as file:
        content = json.load(file)

    assert content == {"test_key": "test_value"}


async def test_empty_memory(temp_memory_file):
    manager = MemoryManager(temp_memory_file)
    assert await manager.list_keys() == []


async def test_multiple_operations(memory_manager):
    await memory_manager.create("key1", "value1")
    await memory_manager.create("key2", "value2")
    await memory_manager.update("key1", "new_value1")
    await memory_manager.delete("key2")

    assert await memory_manager.read("key1") == "new_value1"
    assert await memory_manager.read("key2") is None
    assert await memory_manager.list_keys() == ["key1"]


async def test_upsert(memory_manager):
    # Test creating a new key-value pair
    assert await memory_manager.upsert("upsert_key", "initial_value")
    assert await memory_manager.read("upsert_key") == "initial_value"

    # Test updating an existing key
    assert await memory_manager.upsert("upsert_key", "updated_value")
    assert await memory_manager.read("upsert_key") == "updated_value"

    # Verify that upsert always returns True
    assert await memory_manager.upsert("new_key", "new_value")


async def test_reset(memory_manager):
    # Add some data to the memory
    await memory_manager.create("key1", "value1")
    await memory_manager.create("key2", "value2")

    # Reset the memory
    memory_manager.reset()

    # Check if the memory is empty
    assert await memory_manager.list_keys() == []
    assert await memory_manager.read("key1") is None
    assert await memory_manager.read("key2") is None

    # Check if the file is empty (contains an empty JSON object)
    with open(memory_manager.file_path, "r") as file:
        content = json.load(file)
    assert content == {}


async def test_reset(memory_manager):
    # Add some data to the memory
    await memory_manager.create("key1", "value1")
    await memory_manager.create("key2", "value2")

    # Reset the memory
    memory_manager.reset()

    # Check if the memory is empty
    assert await memory_manager.list_keys() == []
    assert await memory_manager.read("key1") is None
    assert await memory_manager.read("key2") is None

    # Check if the file is empty (contains an empty JSON object)
    with open(memory_manager.file_path, "r") as file:
        content = json.load(file)
    assert content == {}
