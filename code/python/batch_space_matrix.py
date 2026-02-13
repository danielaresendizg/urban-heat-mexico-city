import geopandas as gpd
import pandas as pd
from pathlib import Path

# Directorio base: carpeta con subdirectorios por alcaldía
BASE_DIR = Path(
    '/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/'
    'Dissertation/Data/space_matrix/Catastro'
)

# Lista de subcarpetas de alcaldías
ALCALDIAS = [
    'ALVARO_OBREGON', 'AZCAPOTZALCO', 'BENITO_JUAREZ', 'COYOACAN',
    'CUAJIMALPA', 'CUAUHTEMOC', 'GUSTAVO_A_MADERO', 'IZTAPALAPA',
    'TLAHUAC', 'TLALPAN', 'MAGDALENA_CONTRERAS', 'MIGUEL_HIDALGO',
    'MILPA_ALTA', 'VENUSTIANO_CARRANZA', 'XOCHIMILCO'
]

# Acumulación de GeoDataFrames con métricas por predio
gdf_list = []

# Función para procesar una alcaldía
def procesar_alcaldia(alcaldia):
    subdir = BASE_DIR / alcaldia

    # Identificar archivos en la subcarpeta
    poly_shp = next(subdir.glob('*catastro*.shp'))
    props_shp = next(f for f in subdir.glob('*.shp') if f != poly_shp)
    csv_cat = next(subdir.glob('*-catastro.csv'))

    # Cargar y reproyectar capas
    predios = gpd.read_file(poly_shp).to_crs(epsg=32614)
    props = gpd.read_file(props_shp).to_crs(epsg=32614)
    cat_df = pd.read_csv(csv_cat)
    cat_pts = gpd.GeoDataFrame(
        cat_df,
        geometry=gpd.points_from_xy(cat_df.longitud, cat_df.latitud),
        crs='EPSG:4326'
    ).to_crs(epsg=32614)

    # Convertir a tipos numéricos
    props['niveles'] = pd.to_numeric(props['niveles'], errors='coerce')
    cat_pts['superficie_construccion'] = pd.to_numeric(
        cat_pts['superficie_construccion'], errors='coerce'
    )

    # Estadísticas catastrales por predio
    cat_join = gpd.sjoin(cat_pts, predios, how='inner', predicate='within')
    stats_cat = cat_join.groupby('index_right')['superficie_construccion'].agg(
        num_propiedades='count',
        area_construida='sum'
    )

    # Estadísticas de niveles por predio
    props_join = gpd.sjoin(props, predios, how='inner', predicate='within')
    stats_props = props_join.groupby('index_right')['niveles'].agg(
        niveles_media='mean'
    )

    # Calcular área de cada predio
    predios['area_predio'] = predios.geometry.area

    # Combinar estadísticas
    gdf = predios[['geometry', 'area_predio']].join(stats_cat).join(stats_props)
    gdf[['num_propiedades', 'area_construida', 'niveles_media']] = \
        gdf[['num_propiedades', 'area_construida', 'niveles_media']].fillna(0)

    # Indicadores SpaceMatrix
    gdf['GSI'] = gdf['area_construida'] / gdf['area_predio']
    gdf['FSI'] = (gdf['area_construida'] * gdf['niveles_media']) / gdf['area_predio']
    gdf['alcaldia'] = alcaldia

    return gdf.reset_index(drop=True)

# Procesar todas las alcaldías
gdf_list = [procesar_alcaldia(alc) for alc in ALCALDIAS]

# Concatenar y exportar resultados
all_gdf = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True), crs='EPSG:32614')

# Exportar CSV sin geometría
df_out = pd.DataFrame(all_gdf.drop(columns='geometry'))
# Casting de tipos
int_cols = ['num_propiedades']
float_cols = ['area_predio', 'area_construida', 'niveles_media', 'GSI', 'FSI']
for col in int_cols:
    if col in df_out.columns:
        df_out[col] = df_out[col].astype(int)
for col in float_cols:
    if col in df_out.columns:
        df_out[col] = df_out[col].astype(float).round(4)
df_out.to_csv(BASE_DIR / 'reporte_space_matrix_CDMX.csv', index=False)

# Exportar GeoPackage con geometría
all_gdf.to_file(BASE_DIR / 'reporte_space_matrix_CDMX.gpkg', layer='predios', driver='GPKG')

print("Reporte SpaceMatrix regenerado correctamente.")
