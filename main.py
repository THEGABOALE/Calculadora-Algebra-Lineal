from utils.display import mostrar_sistema_ecuaciones
from models.GaussJordan import GaussJordanMethod
from models.CramerMethod import run_crammer
from models.GaussMethod import run_gauss
from models.GaussJordan import run_gauss_jordan

def main():
    run_gauss_jordan()
    
if __name__ == "__main__":
    main()