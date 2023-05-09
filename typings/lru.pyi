from typing import MutableMapping, TypeVar


K = TypeVar("K")
V = TypeVar("V")

class LRU(MutableMapping[K, V]):
    def __init__(self, limit: int) -> None: ...
