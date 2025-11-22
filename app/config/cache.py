import os
import json
import time

CACHE_FILE = ".cache.json"

_memory_cache = {}

MAX_KEYS = 50

def _load_file_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_file_cache(cache: dict):
    try:
        if len(cache) > MAX_KEYS:
            oldest = min(cache.items(), key=lambda x: x[1]["time"])[0]
            del cache[oldest]
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f)
    except Exception:
        pass

def get_cache(key: str, ttl: int = 60, use_file: bool = False, default=None):
    now = time.monotonic()
    if use_file:
        cache = _load_file_cache()
        if key in cache:
            if now - cache[key]["time"] < ttl:
                return cache[key]["value"]
    else:
        data = _memory_cache.get(key)
        if data and (now - data["time"] < ttl):
            return data["value"]
    return default

def set_cache(key: str, value, use_file: bool = False):
    now = time.monotonic()
    if use_file:
        cache = _load_file_cache()
        cache[key] = {"value": value, "time": now}
        _save_file_cache(cache)
    else:
        _memory_cache[key] = {"value": value, "time": now}

def clear_cache():
    global _memory_cache
    _memory_cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            os.remove(CACHE_FILE)
        except Exception:
            pass
