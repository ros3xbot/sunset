import os
import json
import time

# File cache lokal
CACHE_FILE = "cli_cache.json"

# Cache in-memory
_memory_cache = {}

def _load_file_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_file_cache(cache: dict):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f)
    except Exception:
        pass

def get_cache(key: str, ttl: int = 60, use_file: bool = False):
    """
    Ambil data dari cache.
    - ttl: waktu hidup cache (detik)
    - use_file: True untuk cache file, False untuk cache memory
    """
    now = time.time()
    if use_file:
        cache = _load_file_cache()
        if key in cache:
            if now - cache[key]["time"] < ttl:
                return cache[key]["value"]
    else:
        data = _memory_cache.get(key)
        if data and (now - data["time"] < ttl):
            return data["value"]
    return None

def set_cache(key: str, value, use_file: bool = False):
    """
    Simpan data ke cache.
    - use_file: True untuk cache file, False untuk cache memory
    """
    now = time.time()
    if use_file:
        cache = _load_file_cache()
        cache[key] = {"value": value, "time": now}
        _save_file_cache(cache)
    else:
        _memory_cache[key] = {"value": value, "time": now}
