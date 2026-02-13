# contador_ceros.py
import geopandas as gpd
import pandas as pd

# -------------------------------------------
# Configuración
# -------------------------------------------
ruta_gpkg = "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/manzanas_IVS_20250724_con_alcaldia.gpkg"

VARS_X = [
    "pct_0a5", "pct_6a14", "pct_15a64", "pct_65plus", "pct_ethnic_afro", 
    "pct_ethnic_ind", "pct_ethnic_other", "pct_without_disc", "pct_with_disc", 
    "pct_no_school", "pct_elementary_edu", "pct_elementary2_edu", "pct_more_edu", 
    "pct_ocup", "pct_desocup", "pct_inac", "pct_serv_med", "pct_no_serv_med", 
    "pct_pop_auto", "pct_pop_sin_auto", "rel_dependencia_0_14", "rel_h_m"

]

# -------------------------------------------
# Cargar archivo GeoPackage
# -------------------------------------------
print("Leyendo GeoPackage...")
gdf = gpd.read_file(ruta_gpkg)

n_total = len(gdf)
print(f"Total de filas: {n_total:,}\n")

# -------------------------------------------
# Contar ceros por variable
# -------------------------------------------
resumen = []
for var in VARS_X:
    if var not in gdf.columns:
        print(f"⚠️  La columna '{var}' NO existe en el archivo, se omite.")
        continue

    n_ceros = (gdf[var] == 0).sum()
    n_gt0   = (gdf[var] > 0).sum()
    pct_ceros = n_ceros / n_total * 100

    resumen.append({
        "variable": var,
        "n_ceros": n_ceros,
        "pct_ceros": pct_ceros,
        "n_gt0": n_gt0
    })

# -------------------------------------------
# Mostrar resultados ordenados por % de ceros
# -------------------------------------------
resumen_df = pd.DataFrame(resumen).sort_values("pct_ceros", ascending=False)

print("Resumen de ceros por variable:")
print(resumen_df.to_string(index=False, 
                           formatters={
                               "n_ceros": "{:,}".format,
                               "n_gt0": "{:,}".format,
                               "pct_ceros": "{:.2f}%".format
                           }))
