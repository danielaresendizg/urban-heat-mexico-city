#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
segment_thermal.py
Extrae variables térmicas desde TIFF hacia segmentos (líneas o buffers),
crea métricas (mean/max) y la categoría 'peligro_cat', y guarda salida en GPKG y CSV.

Requiere:
  conda install -c conda-forge geopandas rasterio rasterstats shapely pyproj rtree
o
  python -m pip install geopandas rasterio rasterstats shapely pyproj rtree
"""

from pathlib import Path
import warnings
import geopandas as gpd
import pandas as pd
from rasterio import open as rio_open
from rasterstats import zonal_stats

# ================== CONFIGURA TUS RUTAS ========================
DIR_STREETS = Path("/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/street_network")
DIR_RASTERS = Path("/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/Heat")

# Busca un shapefile de segmentos (ajusta el patrón si el nombre es otro)
CANDIDATOS = list(DIR_STREETS.glob("**/*segment*analysis*.shp")) or list(DIR_STREETS.glob("**/*segment*.shp"))
if not CANDIDATOS:
    raise FileNotFoundError("No encontré shapefiles de segmentos en la carpeta street_network. Ajusta el patrón de búsqueda.")
SEGMENT_SHP = CANDIDATOS[0]

OUT_GPKG = SEGMENT_SHP.with_name("segmentos_con_termico.gpkg")
OUT_CSV  = SEGMENT_SHP.with_name("segmentos_con_termico.csv")

# Ráster a extraer: archivo → estadísticas → nombres finales
SPECS = [
    {"path": DIR_RASTERS / "Albedo_clim.tif",   "stats": ["mean"],       "rename": {"mean": "Albedo_mean"}},
    {"path": DIR_RASTERS / "LST_day_clim.tif",  "stats": ["mean"],       "rename": {"mean": "LST_mean"}},
    {"path": DIR_RASTERS / "NDVI_clim.tif",     "stats": ["mean"],       "rename": {"mean": "NDVI_mean"}},
    {"path": DIR_RASTERS / "NDBI_clim.tif",     "stats": ["mean"],       "rename": {"mean": "NDBI_mean"}},
    {"path": DIR_RASTERS / "UHI_air_clim.tif",  "stats": ["mean","max"], "rename": {"mean": "UHI_mean", "max": "UHI_max"}},
    {"path": DIR_RASTERS / "Ta_clim.tif",       "stats": ["mean","max"], "rename": {"mean": "Ta_mean",  "max": "Ta_max"}},
]

# ================== PARÁMETROS ================================
BUFFER_M   = 10.0   # metros para líneas; pon 0 si ya son buffers (polígonos)
CHUNK_SIZE = 1000   # procesa por lotes para no atascarse
VERBOSE    = True

# ================== HELPERS ==================================
def son_lineas(gdf: gpd.GeoDataFrame) -> bool:
    tipos = set(gdf.geometry.geom_type.unique())
    return tipos.issubset({"LineString", "MultiLineString"})

def extraer_stats(gdf_in: gpd.GeoDataFrame, raster_path: Path, stats, rename_map, buffer_m=0.0) -> gpd.GeoDataFrame:
    """Extrae stats desde un ráster hacia las geometrías, con buffer en CRS métrico y procesamiento por lotes."""
    if not raster_path.exists():
        print(f"⚠️ No encontrado: {raster_path.name} → salto")
        return gdf_in

    with rio_open(raster_path) as ds:
        r_crs  = ds.crs
        nodata = ds.nodata if ds.nodata is not None else -9999

    if r_crs is None:
        raise ValueError(f"El ráster {raster_path.name} no tiene CRS. Asigna uno antes de continuar.")

    # Geometrías en CRS del ráster (lo que pide rasterstats)
    gdf_raster = gdf_in.to_crs(r_crs).copy()

    # Preparar geometrías a muestrear: si son líneas y se pide buffer, hazlo en CRS MÉTRICO (UTM) y regresa al CRS del ráster
    geoms = gdf_raster.geometry
    if son_lineas(gdf_in) and buffer_m and buffer_m > 0:
        try:
            metric_crs = gdf_in.estimate_utm_crs()  # UTM local
        except Exception:
            metric_crs = "EPSG:3857"  # respaldo métrico
        if VERBOSE:
            print(f"   · bufferizando {buffer_m} m en {metric_crs}…")
        gdf_metric = gdf_in.to_crs(metric_crs)
        # Evita warning de buffer en CRS geográfico
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            buffers = gdf_metric.geometry.buffer(buffer_m, cap_style=2)
        geoms = gpd.GeoSeries(buffers, crs=metric_crs).to_crs(r_crs)

    # Inicializa columnas de salida
    cols_finales = {s: rename_map.get(s, f"{raster_path.stem}_{s}") for s in stats}
    for col in cols_finales.values():
        gdf_raster[col] = pd.NA

    n = len(gdf_raster)
    if VERBOSE:
        print(f"   · extrayendo {stats} de {raster_path.name} en {n} segmentos (chunks de {CHUNK_SIZE})")

    # Procesar por tandas
    for i in range(0, n, CHUNK_SIZE):
        j = min(i + CHUNK_SIZE, n)
        if VERBOSE:
            print(f"     [{i:>6}-{j:>6})", end="\r")
        zs = zonal_stats(
            geoms.iloc[i:j],
            raster_path.as_posix(),
            stats=stats,
            nodata=nodata,
            all_touched=False
        )
        for s in stats:
            col = cols_finales[s]
            gdf_raster.loc[gdf_raster.index[i:j], col] = [d.get(s) for d in zs]
    if VERBOSE:
        print("")  # salto de línea después del progreso

    return gdf_raster.to_crs(gdf_in.crs)

def clasificar_peligro(ta):
    """Devuelve 1 si 26 ≤ Ta_mean < 28; 2 si Ta_mean ≥ 28; 0 en otros casos o NaN."""
    if pd.isna(ta):
        return 0
    if 26 <= ta < 28:
        return 1
    if ta >= 28:
        return 2
    return 0

# ================== PROCESO ===================================
def main():
    # Leer segmentos
    gdf = gpd.read_file(SEGMENT_SHP)
    print(f"Segmentos: {len(gdf)} | tipos geom: {set(gdf.geometry.geom_type.unique())}")

    # (Opcional) reparar geometrías inválidas si fueran polígonos
    if {"Polygon","MultiPolygon"} & set(gdf.geometry.geom_type.unique()):
        if not gdf.geometry.is_valid.all():
            print("   · corrigiendo polígonos inválidos con buffer(0)…")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                gdf["geometry"] = gdf.buffer(0)

    out = gdf.copy()

    # Extraer ráster uno por uno
    for spec in SPECS:
        print(f"→ {spec['path'].name} : {spec['stats']}")
        out = extraer_stats(out, spec["path"], spec["stats"], spec["rename"], buffer_m=BUFFER_M)

    # Clasificación de peligro a partir de Ta_mean
    out["peligro_cat"] = out["Ta_mean"].apply(clasificar_peligro).astype(int)

    # Reordenar columnas clave al final (mantiene todas las originales)
    orden_cols = ["Albedo_mean","LST_mean","NDVI_mean","NDBI_mean","UHI_mean","UHI_max","Ta_mean","Ta_max","peligro_cat"]
    cols_pres = [c for c in orden_cols if c in out.columns]
    out = out[[c for c in out.columns if c not in cols_pres] + cols_pres]

    # ---------- Guardar: GPKG ----------
    layer_name = "segments"
    out.to_file(OUT_GPKG, layer=layer_name, driver="GPKG")
    print(f"✅ GPKG guardado: {OUT_GPKG} (capa '{layer_name}')")

    # ---------- Guardar: CSV (sin geometría, con lon/lat del centroide) ----------
    # Calcula centroides en CRS métrico y convierte a WGS84 para lon/lat
    try:
        metric_crs = out.estimate_utm_crs()
    except Exception:
        metric_crs = "EPSG:3857"
    geoms_metric = out.to_crs(metric_crs).geometry
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        centroids_metric = geoms_metric.centroid
    centroids_wgs84 = gpd.GeoSeries(centroids_metric, crs=metric_crs).to_crs(4326)
    out_csv = out.drop(columns="geometry").copy()
    out_csv["lon"] = centroids_wgs84.x.values
    out_csv["lat"] = centroids_wgs84.y.values
    out_csv.to_csv(OUT_CSV, index=False)
    print(f"✅ CSV guardado: {OUT_CSV} (incluye lon/lat del centroide)")

if __name__ == "__main__":
    main()
