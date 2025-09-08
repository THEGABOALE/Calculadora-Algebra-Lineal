# Documentación del Método de Gauss–Jordan (RREF)

> **Repositorio / Archivos:**  
> `models/GaussJordan.py`  
> (apoya en) `models/system_solver/GaussSolver.py` y `utils/printMethods.py`

Documento técnico y pedagógico que describe la implementación del método de **Gauss–Jordan** incluida en el proyecto. Cubre la API, comportamiento, registro de pasos (`frame`), consideraciones numéricas y ejemplos de uso.

---

# 1. Resumen general

El módulo implementa **Gauss–Jordan** para sistemas lineales:

- Trabaja **siempre** sobre la **matriz aumentada** `[A | b]`.
- Realiza:
  1) **Eliminación hacia adelante** (triangulación superior: ceros *debajo* del pivote).  
  2) **Normalización + eliminación hacia atrás** hasta **RREF** (pivotes = 1 y ceros *arriba* y *abajo*).

El diseño separa responsabilidades:

1. `GaussJordanMethod` — operaciones elementales, selección de pivotes, **RREF** y **logging** del proceso en `self.frame`.  
2. `GaussSolver` — análisis del sistema a partir de una aumentada triangular/RREF (rank, pivotes, básicas/libres, inconsistencias) y **cálculo de una solución particular** (fijando variables libres = 0).

Las utilidades de `utils.printMethods` permiten imprimir el proceso y el sistema en forma algebraica.

---

# 2. Archivo: `models/GaussJordan.py` — API y comportamiento

## Constructor

```py
GaussJordanMethod(matriz: List[List[float]], b: Optional[List[float]])