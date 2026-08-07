"""
Traduce el `frame` de core/ (lista ordenada de Step, ver
utils/printMethods.py) a las dos formas que el contrato web espera. Todas las
fases siguientes que expongan un método de core/ con frame reusan esto: es el
único lugar que sabe cómo se ve un Step por fuera.

Verificado contra un frame real de 15 pasos (core/matrix_tools.inverse sobre
una 3x3), no sólo contra un caso trivial de un paso.

core/ no sabe que existe este módulo -- la regla de corte del proyecto
(core/ calcula, no formatea para HTTP) se mantiene igual que se mantuvo con
utils/printMethods.py y utils/html_display.py para el CLI y la web de
templates.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

Step = Dict[str, Any]
Frame = List[Step]


def frame_to_steps(frame: Optional[Frame]) -> List[Dict[str, Any]]:
    """Frame -> lista plana de pasos con el vocabulario del contrato web.

    Cada Step de core/ es {index, text, matrix, det, tag, extra}. El
    frontend (ResultPretty.tsx: `s.operation`, `s.matrix`) espera `operation`
    en vez de `text`; el resto pasa sin tocar, incluida `matrix` como
    lista de listas cruda -- ResultPretty la acepta directo
    (`renderMatrixObject` cae al último caso, `Array.isArray(matrixObj)`,
    cuando no encuentra ninguna de las claves `augmented`/`square`/`extended`/
    `minor`).

    Usado por los métodos cuya respuesta ya es "steps: [...]" plano (Gauss,
    Gauss-Jordan en fases siguientes). `matrix/operate` con las 7 operaciones
    simples NO pasa por acá: esas no producen un frame, sólo un bloque de
    texto (ver adapters/matrices.py).
    """
    if not frame:
        return []
    return [
        {
            "index": step["index"],
            "operation": step["text"],
            "matrix": step["matrix"],
            "det": step["det"],
            "tag": step["tag"],
            "extra": step["extra"],
        }
        for step in frame
    ]


def frame_to_step_states_envelope(frame: Optional[Frame]) -> Dict[str, Any]:
    """Frame -> {"frame": {"step_states": [...]}, "text_steps": [...]}.

    Es el shape que matrix/operate usaba para `inverse` en el repo del que se
    portó el frontend, y ResultPretty.tsx:53 lo prefiere explícitamente:
    `frame?.step_states?.[idx] ?? frame?.states?.[idx]`, alineado por índice
    con `text_steps[idx]`.

    Ahí ese alineamiento salía de dos listas separadas, apendeadas a mano en
    puntos distintos del algoritmo -- con riesgo real de desincronizarse. Acá
    `step_states` y `text_steps` se derivan de la MISMA lista ordenada
    (`frame`), así que el alineamiento por índice no puede romperse: vienen
    de la misma fuente, no de dos.
    """
    frame = frame or []
    return {
        "frame": {
            "step_states": [
                {"matrix": step["matrix"], "det": step["det"], "tag": step["tag"]}
                for step in frame
            ]
        },
        "text_steps": [step["text"] for step in frame],
    }
