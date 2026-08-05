from __future__ import annotations
from typing import List
from utils.EquationFunctions import format_number

class Vector:
    """Vector simple. Operaciones básicas en R^n."""
    def __init__(self, data: List[float]) -> None:
        if not isinstance(data, list) or any(not isinstance(x, (int, float)) for x in data):
            raise ValueError("Vector requiere lista de números.")
        self.data = [float(x) for x in data]

    @property
    def n(self) -> int:
        return len(self.data)

    def copy(self) -> "Vector":
        return Vector(self.data[:])

    # --- operaciones básicas ---
    def add(self, other: "Vector") -> "Vector":
        self._check_same_dim(other)
        return Vector([a + b for a, b in zip(self.data, other.data)])

    def sub(self, other: "Vector") -> "Vector":
        self._check_same_dim(other)
        return Vector([a - b for a, b in zip(self.data, other.data)])

    def scale(self, c: float) -> "Vector":
        return Vector([c * x for x in self.data])

    def dot(self, other: "Vector") -> float:
        self._check_same_dim(other)
        return sum(a * b for a, b in zip(self.data, other.data))

    def equals(self, other: "Vector", tol: float = 1e-12) -> bool:
        if self.n != other.n:
            return False
        return all(abs(a - b) <= tol for a, b in zip(self.data, other.data))

    def _check_same_dim(self, other: "Vector") -> None:
        if self.n != other.n:
            raise ValueError("Dimensiones incompatibles entre vectores.")

    # --- pretty ---
    def __str__(self) -> str:
        return "[" + ", ".join(format_number(x) for x in self.data) + "]"

    def __repr__(self) -> str:
        return f"Vector({self.data})"