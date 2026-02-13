import geopandas as gpd
import pandas as pd
from pathlib import Path

# Directorio base y lista de alcaldías
BASE_DIR = Path(
    '/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/'
    'Dissertation/Data/space_matrix/Catastro'
)
ALCALDIAS = [
    'ALVARO_OBREGON', 'AZCAPOTZALCO', 'BENITO_JUAREZ', 'COYOACAN',
    'CUAJIMALPA', 'CUAUHTEMOC', 'GUSTAVO_A_MADERO', 'IZTAPALAPA',
    'TLAHUAC', 'TLALPAN', 'MAGDALENA_CONTRERAS', 'MIGUEL_HIDALGO',
    'MILPA_ALTA', 'VENUSTIANO_CARRANZA', 'XOCHIMILCO'
]

# Cargar capa de edificios una sola vez desde el GeoPackage raíz
BUILDINGS_GPKG = BASE_DIR / '85d_buildings_filtered.gpkg'
building_layer = '85d_buildings_filtered'  # nombre exacto de la capa dentro del GPKG
buildings_all = gpd.read_file(BUILDINGS_GPKG, layer=building_layer).to_crs(epsg=32614)

def procesar_alcaldia(alcaldia):
    subdir = BASE_DIR / alcaldia

    # Identificar archivos de esta alcaldía
    shp_predios = next(subdir.glob('*catastro*.shp'))
    shp_props   = next(f for f in subdir.glob('*.shp') if f != shp_predios)
    csv_cat     = next(subdir.glob('*-catastro.csv'))

    # Cargar y reproyectar predios y propiedades
    predios = gpd.read_file(shp_predios).to_crs(epsg=32614)
    props   = gpd.read_file(shp_props)  .to_crs(epsg=32614)

    # Cargar puntos catastrales
    cat_df = pd.read_csv(csv_cat)
    cat_pts = gpd.GeoDataFrame(
        cat_df,
        geometry=gpd.points_from_xy(cat_df.longitud, cat_df.latitud),
        crs='EPSG:4326'
    ).to_crs(epsg=32614)

    # Convertir niveles a numérico
    props['niveles'] = pd.to_numeric(props['niveles'], errors='coerce')

    # Asignar ID y calcular área de cada predio
    predios = predios.reset_index().rename(columns={'index': 'idx'})
    predios['area_predio'] = predios.geometry.area

    # num_propiedades: contar puntos dentro de cada predio
    stats_cat = (
        gpd.sjoin(cat_pts, predios[['idx','geometry']],
                  how='inner', predicate='within')
        .groupby('idx').size()
        .rename('num_propiedades')
    )

    # area_construida: intersecar edificios_all ↔ predios y sumar áreas
    inter = gpd.overlay(buildings_all, predios[['idx','geometry']], how='intersection')
    inter['area_interseccion'] = inter.geometry.area
    stats_build = (
        inter.groupby('idx')['area_interseccion']
             .sum()
             .rename('area_construida')
    )

    # niveles_media: promedio de niveles dentro de cada predio
    stats_props = (
        gpd.sjoin(props, predios[['idx','geometry']],
                  how='inner', predicate='within')
        .groupby('idx')['niveles']
        .mean()
        .rename('niveles_media')
    )

    # Unir todas las métricas
    gdf = (
        predios[['geometry','area_predio','idx']]
        .join(stats_cat,   how='left', on='idx')
        .join(stats_build, how='left', on='idx')
        .join(stats_props, how='left', on='idx')
    )
    gdf[['num_propiedades','area_construida','niveles_media']] = \
        gdf[['num_propiedades','area_construida','niveles_media']].fillna(0)

    # Calcular índices SpaceMatrix y añadir alcaldía
    gdf['GSI']      = gdf['area_construida'] / gdf['area_predio']
    gdf['FSI']      = (gdf['area_construida'] * gdf['niveles_media']) / gdf['area_predio']
    gdf['alcaldia'] = alcaldia

    return gdf.reset_index(drop=True)

# Procesar todas las alcaldías y concatenar results
gdf_list = [procesar_alcaldia(a) for a in ALCALDIAS]
all_gdf  = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True), crs='EPSG:32614')

# Exportar CSV sin geometría
df_out = all_gdf.drop(columns='geometry')
df_out['num_propiedades'] = df_out['num_propiedades'].astype(int)
for col in ['area_predio','area_construida','niveles_media','GSI','FSI']:
    df_out[col] = df_out[col].round(4)
df_out.to_csv(BASE_DIR / 'reporte_space_matrix_CDMX.csv', index=False)

# Exportar GeoPackage con geometría
all_gdf.to_file(BASE_DIR / 'reporte_space_matrix_CDMX.gpkg',
                layer='predios', driver='GPKG')

print("Reporte SpaceMatrix regenerado correctamente usando la capa 'buildings_filtered'.")
