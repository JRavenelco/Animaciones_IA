from __future__ import annotations

import os
from pathlib import Path


def load_local_env(base_dir: Path, file_name: str = ".env") -> Path:
    env_path = base_dir / file_name
    if not env_path.exists():
        return env_path

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ[key] = value

    return env_path
