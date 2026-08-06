from __future__ import annotations
from typing import Dict, List, Tuple

Matrix = List[List[float]]
_STORE: Dict[str, Matrix] = {}

def _shape(M: Matrix) -> Tuple[int, int]:
    return (len(M), len(M[0]) if M else 0)

def list_names() -> List[str]:
    return list(_STORE.keys())

def save(name: str, M: Matrix) -> None:
    # Guardamos una copia para evitar efectos laterales
    _STORE[name] = [row[:] for row in M]

def get(name: str) -> Matrix | None:
    M = _STORE.get(name)
    return [row[:] for row in M] if M is not None else None

def remove(name: str) -> bool:
    return _STORE.pop(name, None) is not None

def pretty_inventory() -> str:
    if not _STORE:
        return "(memoria vacía)"
    lines = []
    for k, M in _STORE.items():
        r, c = _shape(M)
        lines.append(f" - {k}: {r}x{c}")
    return "\n".join(lines)
