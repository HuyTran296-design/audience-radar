import os
import yaml
from pathlib import Path
from typing import Dict, Any, Union

class ConfigError(Exception):
    pass

def _check_inline_secrets(data: Any, path: str = ""):
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, str):
                lower_k = str(k).lower()
                # Basic heuristic for rejecting inline secrets
                if any(x in lower_k for x in ["token", "secret", "key", "password", "sk-"]):
                    # Wait, if they have the word 'token' in a list of keywords that's fine.
                    # Usually secrets look like random alphanumeric strings or start with known prefixes.
                    # We will enforce a strict check: if the value matches a regex pattern for a key.
                    if len(v) > 16 and not " " in v and v.isalnum():
                        raise ConfigError(f"Inline secret detected at {path}.{k}. Use environment variables instead.")
            _check_inline_secrets(v, f"{path}.{k}" if path else k)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            _check_inline_secrets(item, f"{path}[{i}]")

def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
    try:
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
            
        if data:
            _check_inline_secrets(data)
            
        return data or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {file_path}: {e}")
    except FileNotFoundError:
        raise ConfigError(f"Config file not found: {file_path}")
