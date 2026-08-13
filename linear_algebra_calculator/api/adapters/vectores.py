"""
vectors/operate: las 6 operaciones sobre core/vector.Vector.
vectors/combination: combinación lineal Ax=b sobre core/vector_tools.py,
reusando matrix_reduce (Fase 3) para no reimplementar Gauss-Jordan.

Los vectores llegan como listas planas y se envuelven en core/vector.Vector
para calcular: add/sub/scale/dot ya validan dimensiones ahí (ValueError si
no coinciden), así que el adaptador no duplica esa regla.

`dot` es el caso que cambia de shape: devuelve un escalar, no un vector.
Las otras cinco devuelven {"vector": [...], "vector_pretty": "..."} en
`result`; dot devuelve {"scalar": ..., "scalar_pretty": "..."}. Cada rama
se arma completa por separado en vez de compartir un `result` genérico,
para que quede explícito en el código -- no es un detalle que convenga
esconder detrás de una condición.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.vector import Vector
from core.vector_tools import ax_check, linear_combination_verification_steps
from utils.EquationFunctions import format_number

from .reduce import matrix_reduce

Vec = List[float]

OPERACIONES = ("add", "sub", "escalar", "comb2", "comb3", "dot")


def _vec_pretty(v: Vec) -> str:
    return "[" + ", ".join(format_number(x) for x in v) + "]"


def _pretty_map(vectors: Dict[str, Vec]) -> Dict[str, Any]:
    return {k: {"raw": v, "pretty": _vec_pretty(v)} for k, v in vectors.items()}


def _pretty_scalars(scalars: Dict[str, float]) -> Dict[str, Any]:
    return {k: {"raw": c, "pretty": format_number(c)} for k, c in scalars.items()}


def _diagram_for(
    *,
    u: Optional[Vec] = None,
    v: Optional[Vec] = None,
    w: Optional[Vec] = None,
    res: Optional[Vec] = None,
    c: Optional[float] = None,
    d: Optional[float] = None,
) -> Dict[str, Any]:
    """Estructura para que el frontend dibuje (2D/3D):
    {"vectors": [{label, from, to, emphasis?}, ...]}.

    Es formato de presentación puro -- geometría de flechas desde el origen
    para cada vector involucrado -- no cálculo, así que vive acá y no en
    core/. No hay ningún componente del frontend que la consuma hoy
    (verificado: 'diagram' no aparece en ningún .tsx), pero es la forma que
    ya trae el contrato portado, y no cuesta nada mantenerla disponible.
    """
    out: Dict[str, Any] = {"vectors": []}
    if u is not None:
        out["vectors"].append({"label": "u", "from": [0] * len(u), "to": list(u)})
    if v is not None:
        out["vectors"].append({"label": "v", "from": [0] * len(v), "to": list(v)})
    if w is not None:
        out["vectors"].append({"label": "w", "from": [0] * len(w), "to": list(w)})
    if c is not None and u is not None:
        cu = Vector(u).scale(c).data
        out["vectors"].append({"label": f"{format_number(c)}·u", "from": [0] * len(u), "to": cu})
    if d is not None and v is not None:
        dv = Vector(v).scale(d).data
        out["vectors"].append({"label": f"{format_number(d)}·v", "from": [0] * len(v), "to": dv})
    if res is not None:
        out["vectors"].append({"label": "resultado", "from": [0] * len(res), "to": list(res), "emphasis": True})
    return out


def vector_operate(
    *,
    operation: str,
    vectors: Dict[str, Vec],
    scalars: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    scalars = scalars or {}
    entrada = {"operation": operation, "vectors": _pretty_map(vectors), "scalars": _pretty_scalars(scalars)}

    if operation == "add":
        u, v = Vector(vectors["u"]), Vector(vectors["v"])
        r = u.add(v)
        return {
            "input": entrada,
            "steps": [f"u + v = {u} + {v} = {r}"],
            "result": {"vector": r.data, "vector_pretty": str(r)},
            "diagram": _diagram_for(u=u.data, v=v.data, res=r.data),
        }

    if operation == "sub":
        u, v = Vector(vectors["u"]), Vector(vectors["v"])
        r = u.sub(v)
        return {
            "input": entrada,
            "steps": [f"u - v = {u} - {v} = {r}"],
            "result": {"vector": r.data, "vector_pretty": str(r)},
            "diagram": _diagram_for(u=u.data, v=v.data, res=r.data),
        }

    if operation == "escalar":
        u = Vector(vectors["u"])
        c = scalars["c"]
        r = u.scale(c)
        return {
            "input": entrada,
            "steps": [f"c·u = {format_number(c)} · {u} = {r}"],
            "result": {"vector": r.data, "vector_pretty": str(r)},
            "diagram": _diagram_for(u=u.data, c=c, res=r.data),
        }

    if operation == "comb2":
        u, v = Vector(vectors["u"]), Vector(vectors["v"])
        c, d = scalars["c"], scalars["d"]
        cu, dv = u.scale(c), v.scale(d)
        r = cu.add(dv)
        return {
            "input": entrada,
            "steps": [
                f"c·u = {format_number(c)} · {u} = {cu}",
                f"d·v = {format_number(d)} · {v} = {dv}",
                f"c·u + d·v = {cu} + {dv} = {r}",
            ],
            "result": {"vector": r.data, "vector_pretty": str(r)},
            "diagram": _diagram_for(u=u.data, v=v.data, c=c, d=d, res=r.data),
        }

    if operation == "comb3":
        u, v, w = Vector(vectors["u"]), Vector(vectors["v"]), Vector(vectors["w"])
        c, d = scalars["c"], scalars["d"]
        cv, dw = v.scale(c), w.scale(d)
        r = u.add(cv).add(dw)
        return {
            "input": entrada,
            "steps": [
                f"c·v = {format_number(c)} · {v} = {cv}",
                f"d·w = {format_number(d)} · {w} = {dw}",
                f"u + c·v + d·w = {u} + {cv} + {dw} = {r}",
            ],
            "result": {"vector": r.data, "vector_pretty": str(r)},
            "diagram": _diagram_for(u=u.data, v=v.data, w=w.data, c=c, d=d, res=r.data),
        }

    if operation == "dot":
        # Ojo con las claves: dot usa 'v' y 'w', no 'u' y 'v' como el resto
        # -- así arma el request AlgebraicMethods.tsx en el frontend.
        v, w = Vector(vectors["v"]), Vector(vectors["w"])
        s = v.dot(w)
        terminos = [f"{format_number(a)}·{format_number(b)}" for a, b in zip(v.data, w.data)]
        return {
            "input": {"operation": operation, "vectors": _pretty_map(vectors)},
            "steps": [" + ".join(terminos) + f" = {format_number(s)}"],
            # dot devuelve un escalar, no un vector: 'result' tiene otra
            # forma acá que en las cinco operaciones de arriba.
            "result": {"scalar": s, "scalar_pretty": format_number(s)},
        }

    raise ValueError(f"Operación desconocida: {operation!r}")


def linear_combination(*, A: List[List[float]], b: List[float]) -> Dict[str, Any]:
    """b es combinación lineal de las columnas de A? Resuelve Ax=b con
    Gauss-Jordan (reusando matrix_reduce de Fase 3) y verifica el resultado
    componente a componente con linear_combination_verification_steps."""
    reducido = matrix_reduce(method="gauss-jordan", A=A, b=b)
    summary = reducido["summary"]
    status = summary["status"]
    x_part = summary["solution"]

    ax: List[float] = []
    ok = False
    pasos_verificacion: List[str] = []
    if x_part is not None:
        ax, ok = ax_check(A, x_part, b)
        columnas = [Vector([fila[j] for fila in A]) for j in range(len(A[0]))]
        _, pasos_verificacion = linear_combination_verification_steps(x_part, columnas, b)

    es_combinacion_lineal = status in ("unique", "infinite")
    enunciado = (
        "b es una combinación lineal de las columnas de A"
        if es_combinacion_lineal
        else "b NO es una combinación lineal de las columnas de A"
    )

    return {
        "input": {
            "A": A, "b": b,
            "A_pretty": [[format_number(x) for x in fila] for fila in A],
            "b_pretty": [format_number(x) for x in b],
        },
        "gauss_jordan": {"steps": reducido["steps"], "summary": summary},
        "check": {
            "Ax": ax,
            "Ax_pretty": [format_number(x) for x in ax] if ax else None,
            "b_pretty": [format_number(x) for x in b],
            "ok": ok,
            "verification_steps": pasos_verificacion,
        },
        "result": {
            "is_linear_combination": es_combinacion_lineal,
            "solution_type": status,
            "coefficients_particular": x_part,
            "coefficients_particular_pretty": (
                [format_number(x) for x in x_part] if x_part is not None else None
            ),
            "columns_statement": enunciado,
        },
    }
