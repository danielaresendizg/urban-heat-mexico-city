#!/usr/bin/env python3
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path

# ——— Rutas ———
BASE_DIR       = Path(__file__).parent.resolve()
INPUT_CSV      = BASE_DIR / "85d_buildings.csv"
ALCALDIAS_SHP  = BASE_DIR / "poligonos_alcaldias_cdmx" / "poligonos_alcaldias_cdmx.shp"
OUTPUT_CSV     = BASE_DIR / "85d_buildings_filtered.csv"

# ——— 1) Cargo y uno todos los polígonos de alcaldías ———
print("Cargando polígonos de alcaldías…")
gdf_alc = gpd.read_file(ALCALDIAS_SHP).to_crs(epsg=4326)
union_alc = gdf_alc.unary_union
minx, miny, maxx, maxy = union_alc.bounds
print(f"  → BBOX alcaldías: [{minx:.4f},{miny:.4f}] — [{maxx:.4f},{maxy:.4f}]")

# ——— 2) Preparo CSV de salida ———
if OUTPUT_CSV.exists():
    OUTPUT_CSV.unlink()
first = True

# ——— 3) Itero el CSV por chunks ———
chunksize = 200_000
print("Procesando CSV en chunks y filtrando por coordenadas…")
for i, df in enumerate(pd.read_csv(INPUT_CSV, 
                                   usecols=["latitude","longitude","area_in_meters","confidence","geometry","full_plus_code"],
                                   chunksize=chunksize), start=1):
    # 3a) Filtro rápido por BBOX
    mask = (
        (df["latitude"]  >= miny) & (df["latitude"]  <= maxy) &
        (df["longitude"] >= minx) & (df["longitude"] <= maxx)
    )
    df_bbox = df[mask]
    if df_bbox.empty:
        print(f" Chunk {i}: 0 filas en BBOX")
        continue

    # 3b) Filtro espacial puntual exacto
    pts = gpd.GeoSeries(
        [Point(xy) for xy in zip(df_bbox["longitude"], df_bbox["latitude"])],
        crs="EPSG:4326"
    )
    df_final = df_bbox[pts.within(union_alc).values]

    # 3c) Escribo las filas retenidas
    df_final.to_csv(
        OUTPUT_CSV,
        mode="w" if first else "a",
        header=first,
        index=False
    )
    first = False
    print(f" Chunk {i}: {len(df_final)} filas retenidas")

print(f"\n✅ CSV filtrado listo en: {OUTPUT_CSV}")
