import pandas as pd
from pathlib import Path

# 1) Directorio base: mismo que usas para tu otro script
BASE_DIR = Path(
    '/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/'
    'Dissertation/Data/space_matrix/Catastro'
)

# 2) Recorremos cada subcarpeta (una por alcaldía)
for subdir in sorted(BASE_DIR.iterdir()):
    if not subdir.is_dir():
        continue
    print(f"\n== Contenido de {subdir.name} ==")
    # 3) Listar todos los archivos .shp y .csv
    shp_files = list(subdir.glob('*.shp'))
    csv_files = list(subdir.glob('*.csv'))
    # 4) Mostrar resultados
    if shp_files:
        print("  Shapefiles:")
        for f in shp_files:
            print("   -", f.name)
    else:
        print("  (no hay .shp)")

    if csv_files:
        print("  CSVs:")
        for f in csv_files:
            print("   -", f.name)
    else:
        print("  (no hay .csv)")
