import json
import os
import re
from functools import lru_cache


@lru_cache
def _load_raw():
    path = "config.json"
    with open(path, encoding="utf-8") as f:
        return f.read()


@lru_cache
def _load_json():
    raw = _load_raw()
    return json.loads(raw)


def get_service_config() -> dict:
    return _load_json()["service"]


def get_database_config() -> dict:
    return _load_json()["database"]


def get_minio_config() -> dict:
    return _load_json()["minio"]


def build_database_url() -> str:
    db = get_database_config()
    return f"postgresql+asyncpg://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}"


def get_cors_config_dict() -> dict | None:
    return None
