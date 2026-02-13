import os
from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely import wkt

# === 0. Rutas automáticas según ubicación del script ===
SCRIPT_DIR = Path(__file__).parent.resolve()  # .../space_matrix/Catastro

# Archivos de entrada
OPENBUILDINGS_CSV = SCRIPT_DIR / "85d_buildings.csv"
PREDIOS_GPKG      = SCRIPT_DIR / "reporte_space_matrix_CDMX.gpkg"

# Archivos de salida (se sobrescriben los originales)
SALIDA_CSV  = SCRIPT_DIR / "reporte_space_matrix_CDMX.csv"
SALIDA_GPKG = SCRIPT_DIR / "reporte_space_matrix_CDMX.gpkg"

# === 1. Comprobaciones iniciales ===
print("Working dir:", os.getcwd())
print("CSV Open Buildings:", OPENBUILDINGS_CSV)
if not OPENBUILDINGS_CSV.exists():
    raise FileNotFoundError(f"No encuentro: {OPENBUILDINGS_CSV}")
print("GPKG predios:", PREDIOS_GPKG)
if not PREDIOS_GPKG.exists():
    raise FileNotFoundError(f"No encuentro: {PREDIOS_GPKG}")

# === 2. Cargar Open Buildings ===
print("Cargando Open Buildings…")
ob = pd.read_csv(OPENBUILDINGS_CSV)
ob['geometry'] = ob['geometry'].apply(wkt.loads)
gdf_ob = gpd.GeoDataFrame(ob, geometry='geometry', crs='EPSG:4326')
gdf_ob = gdf_ob.to_crs(epsg=32614)

# === 3. Cargar predios ===
print("Cargando predios…")
predios = gpd.read_file(PREDIOS_GPKG, layer="predios")
predios = predios.to_crs(epsg=32614)
predios = predios.reset_index(drop=True)
predios['predio_id'] = predios.index

# === 4. Spatial join y cálculo de huella ===
print("Cruzando predios con Open Buildings…")
intersecciones = gpd.overlay(gdf_ob, predios, how='intersection')
intersecciones['huella_m2'] = intersecciones.geometry.area

# Suma de huella por predio
huella_por_predio = (
    intersecciones
    .groupby('predio_id')['huella_m2']
    .sum()
    .rename('huella_total_m2')
)

predios = predios.join(huella_por_predio, on='predio_id')
predios['GSI_open_buildings'] = predios['huella_total_m2'] / predios['area_predio']

# === 5. Exportar sobrescribiendo los archivos existentes ===
print("Exportando resultados…")

# A. CSV (sobrescribe reporte_space_matrix_CDMX.csv)
predios[
    ['predio_id', 'area_predio', 'huella_total_m2', 'GSI_open_buildings']
].to_csv(SALIDA_CSV, index=False)

# B. GeoPackage (sobrescribe reporte_space_matrix_CDMX.gpkg)
# Nota: al usar el mismo nombre, se eliminará la capa antigua y se creará la nueva.
predios.to_file(
    SALIDA_GPKG,
    driver="GPKG",
    layer="predios"
)

print(f"✅ CSV → {SALIDA_CSV}")
print(f"✅ GPKG → {SALIDA_GPKG}")
