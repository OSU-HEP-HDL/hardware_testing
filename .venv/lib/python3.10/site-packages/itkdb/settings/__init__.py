from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from simple_settings import settings

load_dotenv(dotenv_path=Path().cwd().joinpath(".env"))

os.environ.setdefault("SIMPLE_SETTINGS", "itkdb.settings.base")

__all__ = ["settings"]
