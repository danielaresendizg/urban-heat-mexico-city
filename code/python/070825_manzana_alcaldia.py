import geopandas as gpd
import pandas as pd

# Rutas de tus archivos
ruta_gpkg = "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/manzanas_IVS_20250724.gpkg"
ruta_csv_mun = "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/ageb_mza_urbana_09_cpv2020/conjunto_de_datos/conjunto_de_datos_ageb_urbana_09_cpv2020.csv"

# Lee los datos
gdf = gpd.read_file(ruta_gpkg)
df_mun = pd.read_csv(ruta_csv_mun, dtype={'ENTIDAD': str, 'MUN': str})

# Extrae la clave de municipio de los primeros 5 dígitos
gdf['ENTIDAD'] = gdf['CVEGEO'].str.slice(0, 2)
gdf['MUN'] = gdf['CVEGEO'].str.slice(2, 5)

# Une con los nombres de municipio/alcaldía
gdf = gdf.merge(df_mun[['ENTIDAD', 'MUN', 'NOM_MUN']].drop_duplicates(), on=['ENTIDAD', 'MUN'], how='left')

# Guarda GeoPackage
salida_gpkg = ruta_gpkg.replace(".gpkg", "_con_alcaldia.gpkg")
gdf.to_file(salida_gpkg, driver="GPKG")

# Guarda como CSV (sin la geometría)
salida_csv = ruta_gpkg.replace(".gpkg", "_con_alcaldia.csv")
gdf.drop(columns="geometry").to_csv(salida_csv, index=False)

print("¡Listo! Guardados:")
print("GeoPackage:", salida_gpkg)
print("CSV:", salida_csv)
