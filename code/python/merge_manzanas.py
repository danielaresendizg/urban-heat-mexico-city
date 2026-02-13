import pandas as pd
import geopandas as gpd
from pathlib import Path

# 1) Ruta base de los datos
base = Path.home() / "Library/CloudStorage" / \
       "OneDrive-UniversityCollegeLondon(2)" / \
       "Dissertation" / "01_data" / "01_Manzana"

# 2) Rutas al CSV y al SHP
csv_path = base / "ageb_mza_urbana_09_cpv2020" / \
           "conjunto_de_datos" / \
           "conjunto_de_datos_ageb_urbana_09_cpv2020.csv"
shp_path = base / "poligono_manzanas_cdmx (1)" / \
           "poligono_manzanas_cdmx.shp"

# 3) Leer CSV manteniendo ceros a la izquierda
df = pd.read_csv(csv_path, dtype=str)

# 4) Normalizar los componentes de la clave geográfica
for col, width in [("ENTIDAD",2), ("MUN",3), ("LOC",4), ("AGEB",4), ("MZA",3)]:
    df[col] = df[col].str.zfill(width)
df["CVEGEO"] = df["ENTIDAD"] + df["MUN"] + df["LOC"] + df["AGEB"] + df["MZA"]

# 5) Convertir a numérico los conteos y el promedio
count_cols = [
    "POBTOT",    # población total
    "POB0_14",   # población 0–14 años
    "P_60YMAS",  # población 60+ años
    "PHOG_IND",  # hogares indígenas
    "POB_AFRO",  # afrodescendientes
    "PSINDER",   # sin afiliación salud
    "PE_INAC",   # económicamente inactivos
    "TVIVHAB",   # viviendas habitadas totales
    "VPH_AGUAFV" # viviendas sin agua entubada
]
avg_cols = ["GRAPROES"]  # promedio de escolaridad

for col in count_cols + avg_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# 6) Calcular proporciones
# 6a) Variables demográficas sobre POBTOT
demo_vars = [c for c in count_cols if c not in ("POBTOT", "TVIVHAB", "VPH_AGUAFV")]
for col in demo_vars:
    df[f"{col}_prop"] = df[col] / df["POBTOT"]

# 6b) Viviendas sin agua sobre TVIVHAB
df["VPH_AGUAFV_prop"] = df["VPH_AGUAFV"] / df["TVIVHAB"]

# 7) Seleccionar campos finales
vars_core = (
    ["CVEGEO"] +
    count_cols +
    avg_cols +
    [f"{c}_prop" for c in demo_vars] +
    ["VPH_AGUAFV_prop"]
)
df2 = df[vars_core].set_index("CVEGEO")

# 8) Leer el shapefile de manzanas
gdf_raw = gpd.read_file(shp_path)

# 9) Reconstruir CVEGEO en el GeoDataFrame si hace falta
if "CVEGEO" not in gdf_raw.columns:
    for col, width in [
        ("CVE_ENT",2), ("CVE_MUN",3),
        ("CVE_LOC",4), ("CVE_AGEB",4),
        ("CVE_MZA",3)
    ]:
        gdf_raw[col] = gdf_raw[col].astype(str).str.zfill(width)
    gdf_raw["CVEGEO"] = (
        gdf_raw["CVE_ENT"] +
        gdf_raw["CVE_MUN"] +
        gdf_raw["CVE_LOC"] +
        gdf_raw["CVE_AGEB"] +
        gdf_raw["CVE_MZA"]
    )

# 10) Hacer join rápido por índice CVEGEO
gdf = gdf_raw.set_index("CVEGEO")
merged = gdf.join(df2, how="left").reset_index()

# 11) Guardar resultado en GeoPackage
out_fp = base / "manzanas_vulnerabilidad_050725.gpkg"
merged.to_file(out_fp, driver="GPKG")
print(f"✅ Guardado: {out_fp}")


