#!/usr/bin/env python3
import pandas as pd
import geopandas as gpd
from shapely import wkt
from pathlib import Path

BASE        = Path(__file__).parent.resolve()
FILTERED_CSV = BASE / "85d_buildings_filtered.csv"
BUILDINGS_GPKG = BASE / "85d_buildings_filtered.gpkg"

print("1️⃣  Cargando CSV filtrado y convirtiendo geometrías…")
df = pd.read_csv(FILTERED_CSV)
df["geometry"] = df["geometry"].apply(wkt.loads)
gdf_buildings = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")

print("2️⃣  Guardando GeoPackage de edificios filtrados…")
gdf_buildings.to_file(
    BUILDINGS_GPKG,
    layer="buildings_filtered",
    driver="GPKG"
)
print(f"✅ GeoPackage creado: {BUILDINGS_GPKG}")
