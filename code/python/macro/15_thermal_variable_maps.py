import geopandas as gpd
import matplotlib.pyplot as plt
import os

# --- Archivos ---
path_manzanas = "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/manzanas_IVS_20250724.gpkg"
path_alcaldias = "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/Boundaries/poligonos_alcaldias_cdmx/poligonos_alcaldias_cdmx.shp"
path_rios = "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/Environment/rios_cdmx/rios_cdmx.shp"

# --- Leer capas ---
gdf = gpd.read_file(path_manzanas)
gdf_alcaldias = gpd.read_file(path_alcaldias)
gdf_rios = gpd.read_file(path_rios)

# --- Revisar proyecciones y reprojectar si es necesario ---
if not gdf.crs == gdf_alcaldias.crs:
    gdf_alcaldias = gdf_alcaldias.to_crs(gdf.crs)
if not gdf_rios.crs == gdf.crs:
    gdf_rios = gdf_rios.to_crs(gdf.crs)

# --- Variables a mapear ---
vars_to_map = [
    ('Ta_mean', 'Temperatura aire (°C)'),
    ('LST_mean', 'LST superficial (°C)'),
    ('NDVI_mean', 'NDVI medio'),
    ('NDBI_mean', 'NDBI medio'),
    ('Albedo_mean', 'Albedo medio'),
    ('UHI_mean', 'UHI aire (z-score)')
]

# --- Paletas sugeridas ---
cmap_dict = {
    'Ta_mean': 'hot',
    'LST_mean': 'magma',
    'NDVI_mean': 'YlGn',
    'NDBI_mean': 'OrRd',
    'Albedo_mean': 'bone',
    'UHI_mean': 'coolwarm'
}

output_dir = "output_mapas_tematicos"
os.makedirs(output_dir, exist_ok=True)

for v, titulo in vars_to_map:
    if v not in gdf.columns:
        print(f'Variable {v} no encontrada.')
        continue

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    
    # --- Alcaldías como base ---
    gdf_alcaldias.boundary.plot(ax=ax, color='black', linewidth=1, alpha=0.7, zorder=1)
    
    # --- Mapear variable ---
    gdf.plot(
        column=v,
        cmap=cmap_dict.get(v, 'viridis'),
        legend=True,
        legend_kwds={
            'label': titulo,
            'orientation': "vertical",
            'shrink': 0.75,
            'pad': 0.02,
            'aspect': 40
        },
        edgecolor='none',
        linewidth=0,
        ax=ax,
        zorder=2,
        missing_kwds={
            "color": "lightgrey",
            "label": "Sin datos"
        }
    )
    
    # --- Ríos (encima) ---
    gdf_rios.plot(ax=ax, color='#3399ff', linewidth=1.3, alpha=0.8, zorder=3, label='Ríos')

    # --- Ajustar extent para enfocar CDMX ---
    gdf_alcaldias.boundary.plot(ax=ax, color='black', linewidth=1, alpha=0.7, zorder=4)
    ax.set_xlim(gdf_alcaldias.total_bounds[0], gdf_alcaldias.total_bounds[2])
    ax.set_ylim(gdf_alcaldias.total_bounds[1], gdf_alcaldias.total_bounds[3])

    # --- Título y detalles visuales ---
    ax.set_title(f"{titulo} por manzana\nCDMX", fontsize=18, pad=14)
    ax.axis('off')
    
    # --- Leyenda manual para ríos si quieres (opcional) ---
    # ax.legend(loc='lower left', fontsize=10, frameon=True)

    # --- Guardar figura ---
    plt.tight_layout()
    plt.savefig(f'{output_dir}/mapa_{v}.png', bbox_inches='tight', dpi=300)
    plt.show()
    plt.close()

print(f"\n¡Listo! Mapas guardados en la carpeta '{output_dir}'.")
