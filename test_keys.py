#!/usr/bin/env python
# -*- coding: utf-8 -*-

from src.utils.jjson import j_loads_ns
from src.ai.gemini.gemini_api_key_state import _SECRETS_DIR, _KEYS_FILE

print(f"Keys file: {_KEYS_FILE}")
print(f"Exists: {_KEYS_FILE.exists()}")

keys_data = j_loads_ns(_KEYS_FILE)
print(f"Type: {type(keys_data)}")
print(f"Is SimpleNamespace: {str(type(keys_data).__name__) == 'SimpleNamespace'}")

if hasattr(keys_data, '__dict__'):
    print(f"vars keys_data keys: {list(vars(keys_data).keys())}")
    print(f"Number of keys: {len(vars(keys_data))}")
    
    for name, data in vars(keys_data).items():
        print(f"  {name}: {type(data)} - {data if isinstance(data, dict) else str(data)[:50]}")
