from core.matrix import Matrix
from core.matrix_tools import rank_of, system_ranks
from typing import Any, Dict, List, Optional
from utils.printMethods import log_step
from utils.EquationFunctions import format_number, num_to_sub
import copy
from math import isfinite

class CramerMethod(Matrix):
    """
    Resuelve sistemas de ecuaciones lineales usando determinantes.
    Funciona para cualquier cantidad de variables definida por el usuario.

    La regla de Cramer resuelve el caso det(A) ≠ 0 (solución única). Con
    det(A) = 0 sólo sirve en una dirección: si algún det(Aᵢ) ≠ 0 el sistema
    es inconsistente. Si todos los det(Aᵢ) son 0 la regla no decide, y la
    clasificación la hace un procedimiento auxiliar que no es Cramer: el
    análisis de rangos de Rouché–Frobenius (ver `_clasificar_por_rangos`).
    """
    
    def __init__(self, matriz: List[List[float]], b: List[float]) -> None:
        if len(b) != len(matriz):
            raise ValueError("Las variables independientes deben tener la misma cantidad que el numero de ecuaciones")
        
        n = len(matriz)
        # comprobar que cada fila tenga longitud n (matriz n x n)
        if any(len(row) != n for row in matriz):
            raise ValueError("CramerMethod sólo acepta matrices cuadradas (n x n). La matriz recibida no es cuadrada.")
        
        self.matrix_A = copy.deepcopy(matriz)
        self.vector_b = copy.deepcopy(b)
        self.n_variables: int = len(matriz)
        
        self.tolerance: float=1e-12
        
        self.frame: List[Dict[str, Any]] = []
        
        self.determinant_A: Optional[float] = None
        self.solution: Optional[List[float]] = None
    
    #-----------------------
    # DETERMINANTE - REGLA DE SARRUS (solo 3x3)
    #-----------------------
    def calculate_determinant_sarrus(self, matrix: List[List[float]]) -> float:
        """
        Calcula el determinante usando la Regla de Sarrus (solo matrices 3x3).
        Muestra paso a paso las diagonales y productos.
        """
        n = len(matrix)
        if n != 3:
            raise ValueError("La Regla de Sarrus solo aplica para matrices 3x3")

        log_step(self.frame, "═══ MÉTODO: REGLA DE SARRUS (3×3) ═══", matrix, det=None, tag="sarrus_start")

        # Extender matriz (agregar primeras 2 columnas al final)
        extended = [row[:] + row[:2] for row in matrix]
        log_step(self.frame, "Paso 1: Extender matriz (agregar primeras 2 columnas)", extended, det=None, tag="sarrus_extended")

        a11, a12, a13 = matrix[0]
        a21, a22, a23 = matrix[1]
        a31, a32, a33 = matrix[2]

        # Diagonales positivas
        d1_pos = a11 * a22 * a33
        d2_pos = a12 * a23 * a31
        d3_pos = a13 * a21 * a32
        positive = d1_pos + d2_pos + d3_pos

        log_step(self.frame, f"Paso 2: Diagonales principales (↘):", matrix, det=None, tag="sarrus_pos")
        log_step(self.frame, f"  Diagonal 1: ({format_number(a11)})×({format_number(a22)})×({format_number(a33)}) = {format_number(d1_pos)}", matrix, det=None, tag="sarrus_d1")
        log_step(self.frame, f"  Diagonal 2: ({format_number(a12)})×({format_number(a23)})×({format_number(a31)}) = {format_number(d2_pos)}", matrix, det=None, tag="sarrus_d2")
        log_step(self.frame, f"  Diagonal 3: ({format_number(a13)})×({format_number(a21)})×({format_number(a32)}) = {format_number(d3_pos)}", matrix, det=None, tag="sarrus_d3")
        log_step(self.frame, f"  Suma positiva: {format_number(d1_pos)} + {format_number(d2_pos)} + {format_number(d3_pos)} = {format_number(positive)}", matrix, det=None, tag="sarrus_sum_pos")

        # Diagonales negativas
        d1_neg = a13 * a22 * a31
        d2_neg = a11 * a23 * a32
        d3_neg = a12 * a21 * a33
        negative = d1_neg + d2_neg + d3_neg

        log_step(self.frame, f"Paso 3: Diagonales secundarias (↙):", matrix, det=None, tag="sarrus_neg")
        log_step(self.frame, f"  Diagonal 1: ({format_number(a13)})×({format_number(a22)})×({format_number(a31)}) = {format_number(d1_neg)}", matrix, det=None, tag="sarrus_d4")
        log_step(self.frame, f"  Diagonal 2: ({format_number(a11)})×({format_number(a23)})×({format_number(a32)}) = {format_number(d2_neg)}", matrix, det=None, tag="sarrus_d5")
        log_step(self.frame, f"  Diagonal 3: ({format_number(a12)})×({format_number(a21)})×({format_number(a33)}) = {format_number(d3_neg)}", matrix, det=None, tag="sarrus_d6")
        log_step(self.frame, f"  Suma negativa: {format_number(d1_neg)} + {format_number(d2_neg)} + {format_number(d3_neg)} = {format_number(negative)}", matrix, det=None, tag="sarrus_sum_neg")

        det = positive - negative
        log_step(self.frame, f"Paso 4: Determinante = ({format_number(positive)}) - ({format_number(negative)}) = {format_number(det)}", matrix, det=format_number(det), tag="sarrus_result")

        return self._descartar_ruido(matrix, det, tag="sarrus_rounding")

    #-----------------------
    # Ruido de redondeo en un determinante calculado por aritmetica directa
    #-----------------------
    def _descartar_ruido(self, matrix: List[List[float]], det: float, tag: str) -> float:
        """
        Sarrus y cofactores calculan det(A) con sumas y productos directos.
        Con entradas decimales (0.1, 0.2...) que no son representables en
        binario, una matriz singular suele dar ~1e-17 en vez de 0. Antes eso
        quedaba oculto porque format_number mostraba cualquier |x| < 1e-9
        como "0"; ahora se muestra el valor real, así que hay que decir qué
        es. Si la matriz es numéricamente singular (rango < n, el mismo
        criterio que core/matrix_tools.py), se agrega un paso que lo explica
        y se devuelve 0.0. Si no lo es, el valor calculado se respeta por
        chico que sea: det(1e-5·I) = 1e-15 no es ruido.
        """
        if det == 0.0 or rank_of(matrix) == len(matrix):
            return det
        log_step(
            self.frame,
            f"El resultado {format_number(det)} es ruido de redondeo de la aritmética en coma flotante: "
            f"la matriz es numéricamente singular (rango < {len(matrix)}), así que det = 0",
            matrix, det="0", tag=tag,
        )
        return 0.0

    #-----------------------
    # DETERMINANTE - EXPANSIÓN POR COFACTORES
    #-----------------------
    def calculate_determinant_cofactors(self, matrix: List[List[float]], level: int = 0, show_steps: bool = True) -> float:
        """
        Calcula el determinante usando Expansión por Cofactores.
        Muestra paso a paso los cofactores y signos.
        """
        n = len(matrix)

        if level == 0 and show_steps:
            log_step(self.frame, "═══ MÉTODO: EXPANSIÓN POR COFACTORES ═══", matrix, det=None, tag="cofactor_start")
            log_step(self.frame, f"Matriz {n}×{n} - Expandiendo por la primera fila", matrix, det=None, tag="cofactor_expand")

        # Caso base: matriz 1x1
        if n == 1:
            return matrix[0][0]

        # Caso base: matriz 2x2
        if n == 2:
            det = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
            if show_steps and level > 0:
                log_step(self.frame, f"  {'  '*level}Submatriz 2×2: det = ({format_number(matrix[0][0])})×({format_number(matrix[1][1])}) - ({format_number(matrix[0][1])})×({format_number(matrix[1][0])}) = {format_number(det)}", matrix, det=format_number(det), tag=f"cofactor_2x2_level{level}")
            if level == 0 and show_steps:
                return self._descartar_ruido(matrix, det, tag="cofactor_rounding")
            return det

        # Caso recursivo: expansión por la primera fila
        det = 0
        cofactor_details = []

        for j in range(n):
            # Signo del cofactor
            sign = (-1) ** j
            sign_str = "+" if sign > 0 else "-"

            # Elemento de la primera fila
            element = matrix[0][j]

            # Crear submatriz eliminando fila 0 y columna j
            submatrix = [[matrix[i][k] for k in range(n) if k != j] for i in range(1, n)]

            if show_steps and level == 0:
                log_step(self.frame, f"Cofactor C₁{num_to_sub(j+1)}: signo = {sign_str}, elemento = {format_number(element)}", submatrix, det=None, tag=f"cofactor_c1{j+1}")

            # Calcular determinante de la submatriz recursivamente
            sub_det = self.calculate_determinant_cofactors(submatrix, level + 1, show_steps=False)

            # Calcular cofactor
            cofactor = sign * element * sub_det
            det += cofactor

            if show_steps and level == 0:
                log_step(self.frame, f"  C₁{num_to_sub(j+1)} = ({sign_str}1) × ({format_number(element)}) × det(M₁{num_to_sub(j+1)}) = ({sign_str}1) × ({format_number(element)}) × ({format_number(sub_det)}) = {format_number(cofactor)}", submatrix, det=format_number(sub_det), tag=f"cofactor_calc_c1{j+1}")

            cofactor_details.append(f"{sign_str}{format_number(abs(cofactor))}")

        if show_steps and level == 0:
            log_step(self.frame, f"Determinante = {' '.join(cofactor_details)} = {format_number(det)}", matrix, det=format_number(det), tag="cofactor_result")

        if level == 0 and show_steps:
            return self._descartar_ruido(matrix, det, tag="cofactor_rounding")
        return det

    #-----------------------
    # DETERMINANTE (expansion de cofactores)
    #-----------------------
    def calculate_determinant(self, matrix: List[List[float]], show_sarrus: bool = False) -> float :
        n = len(matrix)
        
        # Caso base: matriz 1x1
        if n == 1:
            return matrix[0][0]
        
        # Caso base: matriz 2x2
        if n == 2:
            return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
        
        if n==3:
            if show_sarrus:
                extended = [row[:] for row in matrix] + [matrix[0][:], matrix[1][:]]
                log_step(self.frame, "Sarrus - Matriz Extendida", extended, det=None, tag="sarrus")
                
            a11, a12, a13 = matrix[0]
            a21, a22, a23 = matrix[1]
            a31, a32, a33 = matrix[2]
            
            # Regla de Sarrus:
            positive = a11 * a22 * a33 + a12 * a23 * a31 + a13 * a21 * a32
            negative = a13 * a22 * a31 + a11 * a23 * a32 + a12 * a21 * a33
            return positive - negative
        
        # Caso recursivo: expansión por la primera fila
        det = 0
        for j in range(n):
            # Crear submatriz eliminando fila 0 y columna j
            submatrix = [[matrix[i][k] for k in range(n) if k!=j]for i in range(1,n)]
            
            cofactor = ((-1) ** j) * matrix[0][j] * self.calculate_determinant(submatrix)
            det += cofactor
        
        return det
    
    #-----------------------
    # Creacion matriz Cramer
    #-----------------------
    def create_cramer_matrix(self, col_index:int)->List[List[float]]:
        cramer_matrix = []
        for i in range(self.n_variables):
            row = []
            for j in range(self.n_variables):
                row.append(self.vector_b[i] if j==col_index else self.matrix_A[i][j])
            cramer_matrix.append(row)
        return cramer_matrix
    
    #-----------------------
    # Resolver Sistema
    #-----------------------
    def solve(self)->Dict[str,Any]:
        """
        Resuelve el sistema de ecuaciones.

        Returns:
            dict con 'status' ('unique' | 'inconsistent' | 'infinite'),
            'solution' (lista [x₁, ..., xₙ] o None si no hay solución única),
            'basic_vars', 'free_vars' y 'determinant' (det(A)).

        No levanta excepción cuando det(A) = 0: lo informa en 'status'.
        """
        self.frame = []
        self.solution = None
        n = self.n_variables
        # Los n determinantes de Cramer tal como se decidieron (0.0 exacto si
        # la matriz Aᵢ es numéricamente singular). api/adapters/reduce.py los
        # muestra desde acá en vez de recalcularlos.
        self.determinants_C: List[float] = []

        # Calculo de determinante
        detA_calculado = self.calculate_determinant(self.matrix_A, show_sarrus=(n == 3))

        # Si det(A) es 0 o no NO se decide por el tamaño del número: det(c·I)
        # = cⁿ, así que 1e-5·I tiene det = 1e-15 y es perfectamente
        # invertible (antes, con |det| <= 1e-12, salía "inconsistente"). Se
        # decide por el rango, con el mismo criterio de cero que usan
        # rank_of / determinant / is_singular de core/matrix_tools.py. A la
        # inversa, una matriz singular tipeada con decimales (0.1, 0.2...)
        # suele dar por aritmética un det de ~1e-17 en vez de 0: es ruido de
        # redondeo, se informa como tal y det(A) se toma como 0.
        singular = rank_of(self.matrix_A) < n
        detA = 0.0 if singular else detA_calculado
        self.determinant_A = detA

        texto_det = "Determinante matriz A"
        if singular and detA_calculado != 0.0:
            texto_det += (f" (la aritmética da {format_number(detA_calculado)}, que es ruido de redondeo: "
                          f"A es numéricamente singular, rango(A) < {n}, así que det(A) = 0)")
        log_step(self.frame, texto_det, self.matrix_A, det=format_number(detA), tag="Determinante A")

        # Si detA != 0 -> solucion unica
        if not singular:
            # Rango completo pero el producto no es representable en coma
            # flotante (p. ej. entradas ~1e-110 en 3x3: det ~1e-330 da 0.0
            # por subdesbordamiento). La regla xᵢ = det(Aᵢ)/det(A) no se puede
            # evaluar; decirlo es mejor que dividir por cero o devolver nan.
            if detA_calculado == 0.0 or not isfinite(detA_calculado):
                raise ValueError(
                    "A es invertible, pero det(A) no es representable en coma flotante "
                    f"(se obtuvo {detA_calculado}): la regla de Cramer no se puede aplicar con "
                    "estas magnitudes. Usá Gauss-Jordan o reescalá el sistema."
                )
            solution: List[float] = []
            for col in range(n):
                C = self.create_cramer_matrix(col)
                detC = self.calculate_determinant(C, show_sarrus=(n == 3))
                xi = detC / detA
                if not isfinite(xi):
                    raise ValueError(
                        f"det(A{num_to_sub(col+1)}) no es representable en coma flotante "
                        f"(se obtuvo {detC}): la regla de Cramer no se puede aplicar con estas magnitudes."
                    )
                self.determinants_C.append(detC)
                log_step(self.frame, f"Matriz Cramer para x{num_to_sub(col+1)}", C, det = format_number(detC), tag=f"cramer_x{col+1}")
                solution.append(xi)
            self.solution = solution
            
            solution_formatted = [format_number(v) for v in solution]
            log_step(self.frame, f"Solucion por regla de Cramer (particular): [{', '.join(solution_formatted)}]",
                    self.matrix_A, det=format_number(detA), tag="solution")
            
            basic_vars = list(range(self.n_variables))
            free_vars: List[int] = []
            log_step(self.frame, f"Variables basicas: {', '.join('x'+num_to_sub(i+1) for i in basic_vars)} | Variables libres: None",
                    self.matrix_A, det=format_number(detA), tag="vars")
            result = {
            'status': 'unique',
            'solution': solution,
            'basic_vars': basic_vars,
            'free_vars': free_vars,
            'determinant': detA
            }
            return result
        
        
        # detA == 0 -> no hay solucion unica. Queda distinguir inconsistente
        # de infinitas. Los det(Ai) se calculan igual: si el sistema fuera
        # compatible con solucion x, b = sum(xj * aj) y, por multilinealidad,
        # det(Ai) = xi * det(A) = 0 para todo i. Por contrarreciproca, algun
        # det(Ai) != 0 PRUEBA que el sistema es inconsistente.
        # "det(Aᵢ) ≠ 0" se decide igual que det(A): por el rango de Aᵢ.
        algun_no_nulo = False
        for col in range(n):
            C = self.create_cramer_matrix(col)
            detC_calculado = self.calculate_determinant(C, show_sarrus=(n == 3))
            no_nulo = rank_of(C) == n
            detC = detC_calculado if no_nulo else 0.0
            algun_no_nulo = algun_no_nulo or no_nulo
            self.determinants_C.append(detC)
            texto = f"Matriz de Cramer para x{num_to_sub(col+1)}"
            if not no_nulo and detC_calculado != 0.0:
                texto += (f" (la aritmética da {format_number(detC_calculado)}, que es ruido de redondeo: "
                          f"A{num_to_sub(col+1)} es numéricamente singular, así que su det = 0)")
            log_step(self.frame, texto, C,det=format_number(detC), tag=f"cramer_check_x{col+1}")

        if algun_no_nulo:
            log_step(self.frame, "det(A) = 0 y algún det(Aᵢ) ≠ 0 -> sistema inconsistente", self.matrix_A, det=format_number(detA), tag="inconsistent")
            result = {
            'status': 'inconsistent',
            'solution': None,
            # Sin solucion unica no hay 'variables basicas' que reportar: eso
            # es una nocion de Gauss (que pivote quedo, que columna no), y la
            # regla de Cramer no la calcula. list(range(n)) aca seria mentir
            # "todas las variables son basicas" de un sistema que no tiene
            # solucion.
            'basic_vars': [],
            'free_vars': [],
            'determinant': detA
            }
            return result

        # detA == 0 y todos los det(Ai) == 0: la implicacion de arriba NO
        # tiene vuelta, asi que la regla de Cramer no decide. Antes esta rama
        # concluia "infinitas soluciones" sin mas, y eso es falso: con A = 0
        # y b = (1, 0, 0) los n+1 determinantes valen 0 y el sistema dice
        # 0 = 1. (Con rango(A) = n-1 el criterio si alcanzaria; falla cuando
        # rango(A) <= n-2, que en 2x2 es solo A = 0 y en 3x3 ya incluye
        # rango 1.) La clasificacion pasa a un procedimiento auxiliar.
        status = self._clasificar_por_rangos()

        result = {
            'status': status,
            # Antes era el literal 'Crammer' (con una eme de mas): no una
            # solucion, el nombre del metodo. Sin solucion unica no hay
            # particular que mostrar -- None, igual que la rama
            # 'inconsistent' de arriba. Quien necesite distinguir "infinitas"
            # de "inconsistente" ya tiene 'status' para eso.
            'solution': None,
            # Mismo motivo que en la rama 'inconsistent': con infinitas
            # soluciones SI hay variables libres -- justo lo contrario de
            # "todas basicas". El analisis de rangos dice CUANTAS son
            # (n - rango(A)) pero no CUALES; identificarlas es trabajo de
            # Gauss, asi que no se declara ninguna en vez de fingir que se
            # identificaron.
            'basic_vars': [],
            'free_vars': [],
            'determinant': detA
        }
        return result

    #-----------------------
    # Clasificacion auxiliar (no es la regla de Cramer)
    #-----------------------
    def _clasificar_por_rangos(self) -> str:
        """
        Clasifica un sistema con det(A) = 0 y todos los det(Aᵢ) = 0, el
        único caso que la regla de Cramer no puede decidir.

        Usa el teorema de Rouché–Frobenius: Ax = b es compatible si y sólo
        si rango(A) = rango([A|b]). Como det(A) = 0 implica rango(A) < n,
        compatible significa infinitas soluciones.

        No es Cramer: es eliminación por filas sobre la matriz aumentada
        (`core.matrix_tools.system_ranks`, el mismo motor y el mismo
        criterio de cero que rank_of y matrix/properties). Los dos rangos
        salen de UNA eliminación de [A|b], sin normalizar la columna b, así
        que b de otra magnitud que A no altera la decisión. Se registra en el
        frame como un paso aparte, con la matriz [A|b], para que el
        procedimiento muestre que la conclusión no salió de los determinantes.
        """
        n = self.n_variables
        aumentada = [list(row) + [bi] for row, bi in zip(self.matrix_A, self.vector_b)]
        rango_a, rango_ab = system_ranks(self.matrix_A, self.vector_b)

        log_step(
            self.frame,
            "det(A) = 0 y todos los det(Aᵢ) = 0: la regla de Cramer no decide "
            "(el sistema puede ser inconsistente o tener infinitas soluciones). "
            f"Se compara por rangos (Rouché–Frobenius): rango(A) = {rango_a}, rango([A|b]) = {rango_ab}",
            aumentada, det=None, tag="rank_check",
        )

        if rango_ab > rango_a:
            log_step(
                self.frame,
                f"rango(A) = {rango_a} < rango([A|b]) = {rango_ab} -> sistema inconsistente",
                aumentada, det=None, tag="inconsistent",
            )
            return 'inconsistent'

        # rango_a == rango_ab. Llegamos aca solo si rango(A) < n (det(A) se
        # decidio por el mismo rango), asi que compatible = infinitas.
        log_step(
            self.frame,
            f"rango(A) = rango([A|b]) = {rango_a} < {n} -> infinitas soluciones "
            f"({n - rango_a} parámetro(s) libre(s))",
            aumentada, det=None, tag="infinite",
        )
        return 'infinite'


    def verify_solution(self, log: bool = True)->Dict[str, Any]:
        """
        Verifica que la solución encontrada satisfaga todas las ecuaciones.
        
        Returns:
            bool: True si la solución es correcta
        """
        if not self.solution:
            return {'ok':False, 'differences':[]}
        
        diffs: List[float] =[]
        rows_info: List[str] = []
        for i in range(self.n_variables):
            lhs = 0.0
            terms: List[str] =[]
            
            for j in range(self.n_variables):
                coef = self.matrix_A[i][j]
                val = self.solution[j]
                lhs += coef * val
                terms.append(f"{format_number(coef)}*x{num_to_sub(j+1)}")
            rhs = self.vector_b[i]
            diff = abs(lhs-rhs)
            diffs.append(diff)
            rows_info.append((i, lhs, rhs, diff))
            
            if log:
                step = f"Verificacion ecuacion {i+1}: {' + '.join(terms)} = {format_number(rhs)}"
                log_step(self.frame, step, self.matrix_A, det=None, tag="verify")
                log_step(self.frame, f"Resultado: {format_number(lhs)} | Error: {format_number(diff)}", self.matrix_A, det=None, tag="verify")
        ok = all(d <= self.tolerance for d in diffs)
        return {'ok': ok, 'differences': diffs}
    
# Hacer disponible para importación
__all__ = ['CramerMethod']