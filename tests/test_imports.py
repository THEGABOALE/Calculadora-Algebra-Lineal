"""
Script de prueba para verificar las importaciones
Ejecuta este archivo para ver qué importaciones funcionan
"""

import sys
import os

print("=" * 60)
print("DIAGNÓSTICO DE ESTRUCTURA DE CARPETAS")
print("=" * 60)
print(f"\nDirectorio actual: {os.getcwd()}")
print(f"\nContenido del directorio actual:")
for item in os.listdir('.'):
    item_type = "📁" if os.path.isdir(item) else "📄"
    print(f"  {item_type} {item}")

print("\n" + "=" * 60)
print("PRUEBA DE IMPORTACIONES")
print("=" * 60)

# Prueba 1: Intentar importar desde 'models'
print("\n1. Intentando: from models.CramerMethod import CramerMethod")
try:
    from models.CramerMethod import CramerMethod as CM1
    print("   ✅ ÉXITO - CramerMethod está en models/")
    models_works = True
except ImportError as e:
    print(f"   ❌ FALLO - {e}")
    models_works = False

# Prueba 2: Intentar importar desde 'methods'
print("\n2. Intentando: from methods.CramerMethod import CramerMethod")
try:
    from methods.CramerMethod import CramerMethod as CM2
    print("   ✅ ÉXITO - CramerMethod está en methods/")
    methods_works = True
except ImportError as e:
    print(f"   ❌ FALLO - {e}")
    methods_works = False

# Prueba 3: Intentar importar directamente
print("\n3. Intentando: from CramerMethod import CramerMethod")
try:
    from CramerMethod import CramerMethod as CM3
    print("   ✅ ÉXITO - CramerMethod está en la raíz")
    root_works = True
except ImportError as e:
    print(f"   ❌ FALLO - {e}")
    root_works = False

print("\n" + "=" * 60)
print("RECOMENDACIONES")
print("=" * 60)

if models_works:
    print("\n✅ Usar: from models.CramerMethod import CramerMethod")
    print("   Tu archivo está en: models/CramerMethod.py")
elif methods_works:
    print("\n✅ Usar: from methods.CramerMethod import CramerMethod")
    print("   Tu archivo está en: methods/CramerMethod.py")
elif root_works:
    print("\n✅ Usar: from CramerMethod import CramerMethod")
    print("   Tu archivo está en: ./CramerMethod.py (raíz)")
else:
    print("\n❌ No se pudo encontrar CramerMethod.py")
    print("   Verifica que el archivo existe y tiene la clase CramerMethod")

# Verificar si existen las carpetas
print("\n" + "=" * 60)
print("ESTRUCTURA DETECTADA")
print("=" * 60)

folders = ['models', 'methods', 'utils', 'helpers']
for folder in folders:
    if os.path.isdir(folder):
        print(f"\n📁 {folder}/")
        try:
            files = [f for f in os.listdir(folder) if f.endswith('.py')]
            for f in files[:10]:  # Mostrar máximo 10 archivos
                print(f"   📄 {f}")
            if len(files) > 10:
                print(f"   ... y {len(files) - 10} archivos más")
        except Exception as e:
            print(f"   ❌ No se pudo leer: {e}")
    else:
        print(f"\n❌ {folder}/ - No existe")

print("\n" + "=" * 60)