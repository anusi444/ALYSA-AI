import json
import os

MEMORY_FILE = "memory.json"


def save_memory(key, value):
    data = {}
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
    except Exception as e:
        print(f"[Memory] Read error: {e}")

    data[key] = value

    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[Memory] Write error: {e}")


def get_memory(key):
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get(key)
    except Exception:
        return None


def get_all_memories():
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
