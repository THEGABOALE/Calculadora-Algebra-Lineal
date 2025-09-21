
class Matrix():
    def __init__(self, matriz: list[list]) -> None:
        self.matriz = matriz
        self.filas = len(matriz)
        self.columnas = len(matriz[0])
