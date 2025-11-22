import os
import json
import time

# File cache lokal (hidden file)
CACHE_FILE = ".cli_cache.json"

# Cache in-memory
_memory_cache = {}

# Limit jumlah key di file cache
MAX_KEYS = 20

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
        # Batasi jumlah key agar file tidak membesar
        if len(cache) > MAX_KEYS:
            oldest = min(cache.items(), key=lambda x: x[1]["time"])[0]
            del cache[oldest]
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f)
    except Exception:
        pass

def get_cache(key: str, ttl: int = 60, use_file: bool = False, default=None):
    """
    Ambil data dari cache.
    - ttl: waktu hidup cache (detik)
    - use_file: True untuk cache file, False untuk cache memory
    - default: nilai default jika cache kosong/kadaluarsa
    """
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
    """
    Simpan data ke cache.
    - use_file: True untuk cache file, False untuk cache memory
    """
    now = time.monotonic()
    if use_file:
        cache = _load_file_cache()
        cache[key] = {"value": value, "time": now}
        _save_file_cache(cache)
    else:
        _memory_cache[key] = {"value": value, "time": now}

def clear_cache():
    """
    Bersihkan semua cache (memory + file).
    """
    global _memory_cache
    _memory_cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            os.remove(CACHE_FILE)
        except Exception:
            pass
