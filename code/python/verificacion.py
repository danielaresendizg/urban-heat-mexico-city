import geopandas as gpd
import pandas as pd

# Carga los datos
csv = pd.read_csv('reporte_space_matrix_CDMX.csv')
gdf = gpd.read_file('reporte_space_matrix_CDMX.gpkg', layer='predios')

# Asegura que las dos columnas existan y sean int
csv_vals  = csv['num_propiedades'].fillna(0).astype(int)
gpkg_vals = gdf['num_propiedades'].fillna(0).astype(int)

# Comprueba que tengan la misma longitud
print("Predios CSV:", len(csv_vals), "Predios GPKG:", len(gpkg_vals))

# Cuenta discrepancias
mismatch = (csv_vals.values != gpkg_vals.values).sum()
print("Discrepancias en num_propiedades:", mismatch)

if mismatch:
    # Muestra las primeras 5 filas donde difieren
    diffs = pd.DataFrame({
        'csv': csv_vals,
        'gpkg': gpkg_vals
    })
    print(diffs[diffs['csv'] != diffs['gpkg']].head())
