import geopandas as gpd

# Ruta del archivo
ruta_gpkg = "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/manzanas_IVS_heat_20250707.gpkg"

# Cargar el GeoDataFrame
gdf = gpd.read_file(ruta_gpkg)

# Lista de columnas a rellenar con 0 si hay nulos
cols_null_to_zero = [
    "POBTOT", "P_3YMAS", "P_12YMAS", "P_60YMAS", "P_0A2", "P_3A5",
    "P3YM_HLI", "POB_AFRO", "PCON_DISC", "PSINDER",
    "GRAPROES", "PE_INAC", "PRO_OCUP_C",
    "pct_0a5", "pct_60plus", "pct_hli", "pct_afro", "pct_disc", "pct_inac", "pct_no_serv_med"
]

# Reemplazar nulos por 0 SOLO en esas columnas
for col in cols_null_to_zero:
    if col in gdf.columns:
        gdf[col] = gdf[col].fillna(0)

# Solo columnas que existen en el archivo
cols_existing = [col for col in cols_null_to_zero if col in gdf.columns]
print(gdf[cols_existing].isnull().sum())

# (Opcional) Guardar el archivo corregido (puedes cambiar el nombre de salida si quieres)
gdf.to_file(ruta_gpkg.replace(".gpkg", "_sin_nulos.gpkg"), driver="GPKG")
print("Archivo guardado con nulos reemplazados por 0.")
