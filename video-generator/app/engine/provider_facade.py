from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderFacade:
    """Opaque reviewed provider entrypoints; credentials are never exposed."""
    image: Any = None
    voice: Any = None
    codex: Any = None
