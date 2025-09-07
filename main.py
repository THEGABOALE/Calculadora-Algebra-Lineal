from utils.display import mostrar_sistema_ecuaciones
from models.GaussJordan import GaussJordanMethod
from models.CramerMethod import run_crammer
from models.GaussMethod import run_gauss

def main():
    run_crammer()
    
if __name__ == "__main__":
    main()