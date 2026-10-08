#!/usr/bin/env python
# -*- coding: utf-8 -*-

from src.utils.jjson import j_loads_ns
from src.ai.gemini.gemini_api_key_state import _SECRETS_DIR, _KEYS_FILE
from types import SimpleNamespace

print(f"Keys file: {_KEYS_FILE}")
print(f"Exists: {_KEYS_FILE.exists()}")

keys_data = j_loads_ns(_KEYS_FILE)
print(f"Type: {type(keys_data)}")

# Convert SimpleNamespace to dict recursively
if isinstance(keys_data, SimpleNamespace):
    keys_data = {k: vars(v) if isinstance(v, SimpleNamespace) else v 
                for k, v in vars(keys_data).items()}

print(f"keys_data keys: {list(keys_data.keys())}")
print(f"Number of keys: {len(keys_data)}")

for name, data in keys_data.items():
    print(f"  {name}: {type(data)} - status={data.get('status', 'N/A')}")
