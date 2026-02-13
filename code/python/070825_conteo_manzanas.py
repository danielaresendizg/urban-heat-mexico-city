import geopandas as gpd

# Ruta del archivo
ruta = '/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/manzanas_IVS_20250724_con_alcaldia.gpkg'

# Leer el GeoPackage
gdf = gpd.read_file(ruta)

# Contar filas por alcaldía
conteo = (
    gdf.groupby('NOM_MUN')
       .size()
       .reset_index(name='num_filas')
       .sort_values('num_filas', ascending=False)
)

# Mostrar
print("Número de filas por alcaldía:")
for _, row in conteo.iterrows():
    print(f"{row['NOM_MUN']}: {row['num_filas']} filas")

# Si quieres también ver el DataFrame completo:
# print(conteo)
