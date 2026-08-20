import os
from typing import Optional

def resolve_secret(secret_name: str) -> Optional[str]:
    """Resolve a secret from the environment.
    
    Never hard-code secrets.
    """
    return os.getenv(secret_name)
