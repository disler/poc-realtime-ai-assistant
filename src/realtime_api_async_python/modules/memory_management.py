import json
import os
from typing import Any, Dict, Optional, List
import xml.etree.ElementTree as ET
from . import utils


class MemoryManager:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.memory: Dict[str, Any] = {}
        self.load_memory()

    def load_memory(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as file:
                self.memory = json.load(file)
        else:
            self.memory = {}

    def save_memory(self):
        with open(self.file_path, "w") as file:
            json.dump(self.memory, file, indent=2)

    def create(self, key: str, value: Any) -> bool:
        if key not in self.memory:
            self.memory[key] = value
            self.save_memory()
            return True
        return False

    def read(self, key: str) -> Optional[Any]:
        return self.memory.get(key)

    def update(self, key: str, value: Any) -> bool:
        if key in self.memory:
            self.memory[key] = value
            self.save_memory()
            return True
        return False

    def delete(self, key: str) -> bool:
        if key in self.memory:
            del self.memory[key]
            self.save_memory()
            return True
        return False

    def list_keys(self) -> list:
        return list(self.memory.keys())

    def raw_memory(self) -> str:
        return json.dumps(self.memory)

    def upsert(self, key: str, value: Any) -> bool:
        self.memory[key] = value
        self.save_memory()
        return True

    def get_xml_for_prompt(self, keys: List[str]) -> str:

        # reload memory from file
        self.load_memory()

        root = ET.Element("memory")
        matched_keys = False
        for pattern in keys:
            for key in self.memory:
                if utils.match_pattern(pattern, key):
                    child = ET.SubElement(root, key)
                    child.text = str(self.memory[key])
                    matched_keys = True
        return ET.tostring(root, encoding="unicode") if matched_keys else ""

    def reset(self):
        self.memory = {}
        self.save_memory()


# create yaml, sqlite/duckdb memory managers

# Initialize the MemoryManager
memory_file = os.getenv("ACTIVE_MEMORY_FILE", "./active_memory.json")
if not os.path.exists(memory_file):
    with open(memory_file, "w") as f:
        json.dump({}, f)
memory_manager = MemoryManager(memory_file)
