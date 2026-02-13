import geopandas as gpd
import rasterio
from rasterstats import zonal_stats
from pathlib import Path

# === Configuración ===
base_dir = Path("/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana")
vector_path = base_dir / "manzanas_IVS_Ta.gpkg"
layer_name = "manzanas_ivs_ta"
raster_dir = base_dir.parent / "Heat"
raster_files = {
    "LST": raster_dir / "LST_day_clim.tif",
    "NDVI": raster_dir / "NDVI_clim.tif",
    "NDBI": raster_dir / "NDBI_clim.tif",
    "Albedo": raster_dir / "Albedo_clim.tif",
    "UHI": raster_dir / "UHI_air_clim.tif"
}

# === Leer la capa de manzanas ===
gdf = gpd.read_file(vector_path, layer=layer_name)

# === Asegurar mismo CRS que los ráster ===
# Leer CRS de un ráster de referencia
tmp_raster = next(iter(raster_files.values()))
with rasterio.open(tmp_raster) as src:
    raster_crs = src.crs
# Reproyectar capa vectorial si es necesario
if gdf.crs != raster_crs:
    gdf = gdf.to_crs(raster_crs)

# === Calcular estadísticas zonales y agregar a la capa ===
for prefix, raster_path in raster_files.items():
    print(f"Procesando {prefix}...")
    stats = zonal_stats(
        gdf,
        raster_path,
        stats=["mean"],
        geojson_out=True,
        nodata=-9999
    )
    means = [feat["properties"]["mean"] for feat in stats]
    gdf[f"{prefix}_mean"] = means

# === Guardar el resultado en un nuevo GPKG ===
out_path = base_dir / "manzanas_ivs_thermal.gpkg"
gdf.to_file(out_path, layer=layer_name, driver="GPKG")
print(f"✅ Capa guardada con todos los índices térmicos en: {out_path}")

