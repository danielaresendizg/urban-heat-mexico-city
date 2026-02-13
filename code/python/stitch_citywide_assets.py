# -*- coding: utf-8 -*-
"""
Stitch citywide assets (FAST, GPKG-only)

Entrada (ya organizadas por ti):
  <BASE>/alcaldias_shp/                 # 16 shapefiles de límites por alcaldía
  <BASE>/catastro_alcaldias_shp/        # 16 shapefiles de predios: catastro2021_*.shp
  <BASE>/catastro_alcaldias_cvs/        # 16 CSV/XLSX: <alcaldia>-catastro.*

Salida: <BASE>/citywide_build/
  - cdmx_citywide.gpkg (layers):
      * alcaldias
      * predios
      * predios_centroides
      * catastro_puntos
  - cdmx_catastro.csv                   # los mismos puntos pero en CSV para revisión rápida
  - qc_catastro_columns.csv             # auditoría de columnas detectadas por archivo
  - qc_sources.csv                      # auditoría de archivos leídos y conteos

Principios de eficiencia:
  - Sin Shapefile de salida (evita GeometryCollection y límites del driver SHP).
  - Sin dissolve ni buffer(0) globales; solo limpieza mínima y selectiva.
  - Lectura tolerante (CSV/Excel, comas decimales, alias de columnas, WGS84/UTM).
  - Reproyección única a EPSG:32614 solo cuando hace falta.
"""

from pathlib import Path
import pandas as pd
import geopandas as gpd
import numpy as np

# ============== RUTAS (AJUSTADAS A TU CASO) ==============
BASE = Path(
    "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/Data_catastro"
)
ALC_SHPS = BASE / "alcaldias_shp"
CAT_SHPS = BASE / "catastro_alcaldias_shp"
CAT_CSVS = BASE / "catastro_alcaldias_cvs"
OUT_DIR  = BASE / "citywide_build"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_GPKG = OUT_DIR / "cdmx_citywide.gpkg"
CRS_METERS = 32614  # UTM14N

# ============== PARÁMETROS LIGEROS ==============
SKIP_GEOM_FIX = True        # True = más rápido; pon False si detectas geometrías inválidas
MAKE_CENTROIDS = True       # True = genera capa de centroides para futuros joins

# ============== HELPERS ==============
ALIAS_LON = ["longitud","longitude","lon","x","Lon","X"]
ALIAS_LAT = ["latitud","latitude","lat","y","Lat","Y"]
ALIAS_F   = ["superficie_construccion","sup_construccion","superficie_construida",
             "sup_const","superficie_total_construida","sup_total","area_construida"]
ALIAS_T   = ["superficie_terreno","sup_terreno","area_terreno","terreno"]


def _fix_geom_min(g: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Limpieza mínima y selectiva (solo si SKIP_GEOM_FIX=False)."""
    if SKIP_GEOM_FIX:
        # Descarta nulos; mantiene lo demás tal cual
        return g[g.geometry.notna()].copy()
    g = g[g.geometry.notna()].copy()
    if not g.is_valid.all():
        bad = ~g.is_valid
        g.loc[bad, "geometry"] = g.loc[bad, "geometry"].buffer(0)
        g = g[g.geometry.notna()]
    return g


def _name_from_stem(p: Path) -> str:
    return p.stem.upper()


def _alcaldia_from_cat_shp(p: Path) -> str:
    # catastro2021_IZTACALCO.shp -> IZTACALCO
    s = p.stem.upper()
    return s.split("CATASTRO2021_")[-1]


def _read_any_csv(p: Path) -> pd.DataFrame:
    if p.suffix.lower() in (".xls", ".xlsx"):
        return pd.read_excel(p)
    return pd.read_csv(p)


def _coerce_decimals(df: pd.DataFrame, cols: list) -> None:
    for c in cols:
        if c in df.columns and df[c].dtype == object:
            df[c] = df[c].str.replace(",", ".", regex=False)


# ============== 1) UNIR ALCALDÍAS (polígonos) ==============
print("[1/4] Unificando polígonos de alcaldías…")
rows = []
for shp in sorted(ALC_SHPS.glob("*.shp")):
    g = gpd.read_file(shp)
    if g.crs is None:
        g = g.set_crs(CRS_METERS)
    g = g.to_crs(CRS_METERS)
    g = _fix_geom_min(g)
    g = g[["geometry"]].copy()
    g["alcaldia"] = _name_from_stem(shp)
    rows.append(g)

if rows:
    g_alc = gpd.GeoDataFrame(pd.concat(rows, ignore_index=True), crs=CRS_METERS)
else:
    g_alc = gpd.GeoDataFrame(columns=["geometry","alcaldia"], crs=CRS_METERS)

g_alc.to_file(OUT_GPKG, layer="alcaldias", driver="GPKG")
print(f"  → alcaldías: {len(g_alc)} features | capa 'alcaldias' en {OUT_GPKG}")

# ============== 2) UNIR PREDIOS (polígonos) ==============
print("[2/4] Unificando predios (catastro2021_*.shp)…")
rows = []
for shp in sorted(CAT_SHPS.glob("catastro2021_*.shp")):
    try:
        g = gpd.read_file(shp)
    except Exception as e:
        print("  ⚠ no se pudo leer:", shp.name, "→", e)
        continue
    if g.crs is None:
        g = g.set_crs(CRS_METERS)
    g = g.to_crs(CRS_METERS)
    g = _fix_geom_min(g)
    g = g[["geometry"]].copy()
    g["alcaldia"] = _alcaldia_from_cat_shp(shp)
    rows.append(g)

g_pred = gpd.GeoDataFrame(pd.concat(rows, ignore_index=True), crs=CRS_METERS) if rows else \
         gpd.GeoDataFrame(columns=["geometry","alcaldia"], crs=CRS_METERS)

g_pred.to_file(OUT_GPKG, layer="predios", driver="GPKG")
print(f"  → predios: {len(g_pred)} features | capa 'predios'")

if MAKE_CENTROIDS and len(g_pred) > 0:
    print("  · Calculando centroides de predios…")
    g_cent = g_pred.copy()
    g_cent["geometry"] = g_cent.geometry.centroid
    g_cent.to_file(OUT_GPKG, layer="predios_centroides", driver="GPKG")
    print("    → capa 'predios_centroides' lista")

# ============== 3) UNIR CATASTRO (CSV/XLSX) ==============
print("[3/4] Unificando CSV/XLSX de catastro (puntos con superficies)…")
rows, audit = [], []
for f in sorted(CAT_CSVS.glob("*-catastro.*")):
    try:
        df = _read_any_csv(f)
    except Exception as e:
        print("  ⚠ no se pudo leer:", f.name, "→", e)
        continue
    # auditoría de columnas
    audit.append({"archivo": f.name, "columnas": ",".join(sorted(map(str, df.columns)))})

    # normalización de separador decimal
    _coerce_decimals(df, ALIAS_LON + ALIAS_LAT)

    lon = next((c for c in ALIAS_LON if c in df.columns), None)
    lat = next((c for c in ALIAS_LAT if c in df.columns), None)
    F   = next((c for c in ALIAS_F   if c in df.columns), None)
    T   = next((c for c in ALIAS_T   if c in df.columns), None)

    if not (lon and lat):
        print("  ⚠ sin columnas de coord:", f.name)
        continue

    tmp = pd.DataFrame({
        "longitud": pd.to_numeric(df[lon], errors="coerce"),
        "latitud":  pd.to_numeric(df[lat], errors="coerce"),
        "sup_const_tot_m2": pd.to_numeric(df[F], errors="coerce") if F else pd.NA,
        "sup_terreno_tot_m2": pd.to_numeric(df[T], errors="coerce") if T else pd.NA,
    })
    tmp["alcaldia"] = f.stem.split("-catastro")[0].upper().replace("-", "_")

    # descarta registros sin coord
    tmp = tmp.dropna(subset=["longitud","latitud"]).reset_index(drop=True)

    rows.append(tmp)

cat_all = pd.concat(rows, ignore_index=True) if rows else \
          pd.DataFrame(columns=["longitud","latitud","sup_const_tot_m2","sup_terreno_tot_m2","alcaldia"])

# Auditorías
pd.DataFrame(audit).to_csv(OUT_DIR/"qc_catastro_columns.csv", index=False)
(pd.DataFrame({
    "fuente": ["alcaldias_shp","catastro_alcaldias_shp","catastro_alcaldias_cvs"],
    "archivos_leidos": [len(list(ALC_SHPS.glob('*.shp'))),
                         len(list(CAT_SHPS.glob('catastro2021_*.shp'))),
                         len(list(CAT_CSVS.glob('*-catastro.*')))],
}).assign(reg_catastro=len(cat_all))).to_csv(OUT_DIR/"qc_sources.csv", index=False)

# Guardar CSV plano
out_csv = OUT_DIR / "cdmx_catastro.csv"
cat_all.to_csv(out_csv, index=False)
print(f"  → catastro: {len(cat_all)} registros | {out_csv}")

# Guardar puntos en GPKG reproyectados a 32614
print("  · Generando capa 'catastro_puntos' en el GPKG…")
g_cat = gpd.GeoDataFrame(
    cat_all,
    geometry=gpd.points_from_xy(cat_all["longitud"], cat_all["latitud"]),
    crs="EPSG:4326"
)
# Detecta si son grados; si no, asume ya en 32614
try:
    if g_cat.total_bounds[0] >= -180 and g_cat.total_bounds[2] <= 180:
        g_cat = g_cat.to_crs(CRS_METERS)
    else:
        g_cat.set_crs(CRS_METERS, inplace=True)
except Exception:
    g_cat = g_cat.to_crs(CRS_METERS)

g_cat.to_file(OUT_GPKG, layer="catastro_puntos", driver="GPKG")
print(f"    → capa 'catastro_puntos' lista en {OUT_GPKG}")

print("[4/4] Hecho ✅  (GPKG unificado + CSV + auditorías)")
