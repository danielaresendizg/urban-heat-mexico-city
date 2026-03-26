"""
preprocess_maps.py
Generates simplified GeoJSON files for the CDMX Urban Heat interactive atlas.

Strategy: ONE manzanas file with all attributes (geometry shared),
          ONE network file (urban only), ONE priority file.

Usage:
    python3 preprocess_maps.py
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import os
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────
BASE = Path.home() / "Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data"
MANZANA_GPKG = Path(
    os.environ.get(
        "MANZANA_GPKG",
        str(BASE / "01_Manzana/manzanas_thermal_GWR_spacematrix_hotspots_final.gpkg"),
    )
)
ZONES_GPKG = Path(
    os.environ.get(
        "ZONES_GPKG",
        str(BASE / "01_Manzana/analisis_final_tipologias_syntaxONLY_20250816_0042.gpkg"),
    )
)
SEGMENTS_GPKG = Path(
    os.environ.get(
        "SEGMENTS_GPKG",
        str(BASE / "street_network/segmentos_con_termico.gpkg"),
    )
)
OUT = Path(__file__).parent / "data"

SIMPLIFY_MANZANA = 25   # metres — aggressive, still readable at borough level
SIMPLIFY_NETWORK = 15
COORD_PRECISION = 4      # ~11m precision — fine for city-scale viewing


def process_and_save(gdf, path, simplify_tol):
    """Simplify, reproject, round numeric columns, save."""
    # Simplify in projected CRS
    if gdf.crs and not gdf.crs.is_geographic:
        gdf["geometry"] = gdf.geometry.simplify(simplify_tol, preserve_topology=True)
    # Remove empty/null geometries
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()]
    # Reproject
    gdf = gdf.to_crs(epsg=4326)
    # Round numeric columns to 2 decimals to save space
    for col in gdf.select_dtypes(include=[np.floating]).columns:
        gdf[col] = gdf[col].round(2)
    # Save
    gdf.to_file(path, driver="GeoJSON", coordinate_precision=COORD_PRECISION)
    size_mb = os.path.getsize(path) / 1e6
    print(f"  -> {path.name}: {len(gdf)} features, {size_mb:.1f} MB")
    return size_mb


# ── 1. MANZANAS — all attributes in one file ─────────────────────────────────
def export_manzanas():
    print("\n[1/3] Manzanas (all attributes)...")

    # Read the typology v2 layer (has most columns including typology)
    gdf = gpd.read_file(MANZANA_GPKG, layer="manzanas_typology_SM_v2")
    print(f"  Loaded: {len(gdf)} features, {len(gdf.columns)} columns")

    # Select columns we need
    keep = [
        # ID
        "CVEGEO", "NOM_MUN",
        # Thermal
        "Ta_mean", "Ta_max", "LST_mean", "UHI_mean", "NDVI_mean",
        "Albedo_mean", "NDBI_mean",
        # Social vulnerability
        "pct_0a5", "pct_6a14", "pct_65plus",
        "pct_ethnic_ind", "pct_ethnic_afro",
        "pct_with_disc",
        "pct_pop_sin_auto",
        "pct_no_serv_med",
        "pct_inac", "pct_desocup",
        "pct_no_school", "pct_elementary_edu",
        "rel_dependencia_0_14",
        # Hotspots
        "peligro_cat",
        "is_hot_26", "is_hot_28",
        "hot26_pct_65plus", "hot26_pct_6a14",
        "hot26_pct_with_disc", "hot26_pct_pop_sin_auto",
        "hot26_pct_no_serv_med", "hot26_pct_inac",
        "hot26_pct_elementary_edu",
        "hot26_count_social",
        "hot28_pct_65plus", "hot28_pct_6a14",
        "hot28_pct_with_disc", "hot28_pct_pop_sin_auto",
        "hot28_pct_no_serv_med", "hot28_pct_inac",
        "hot28_pct_elementary_edu",
        "hot28_count_social",
        # Morphology
        "FSI", "GSI", "L_equiv", "OSR",
        "typology_sm_final",
        # Geometry
        "geometry",
    ]
    keep = [c for c in keep if c in gdf.columns]
    gdf = gdf[keep]

    # Convert integer hotspot columns to int8 to save space
    int_cols = [c for c in gdf.columns if c.startswith(("is_hot", "hot26_", "hot28_"))]
    for col in int_cols:
        gdf[col] = gdf[col].fillna(0).astype(np.int8)

    process_and_save(gdf, OUT / "manzanas.geojson", SIMPLIFY_MANZANA)


# ── 2. STREET NETWORK (Space Syntax + thermal from gpkg) ─────────────────────
def export_network():
    print("\n[2/3] Street network (Space Syntax + thermal)...")

    # Read from segmentos_con_termico.gpkg — has geometry + syntax + thermal
    segs = gpd.read_file(SEGMENTS_GPKG, layer="segments")
    print(f"  Segments loaded: {len(segs)}")

    # Keep only relevant columns
    keep = ["NACHr500m", "NACHr1500m", "NACHr5000m",
            "NAINr500m", "NAINr1500m", "NAINr5000m",
            "Ta_mean", "LST_mean", "NDVI_mean", "UHI_mean",
            "Albedo_mean", "peligro_cat",
            "geometry"]
    keep = [c for c in keep if c in segs.columns]
    segs = segs[keep]

    # Ensure numeric columns are actually numeric (not strings from GPKG)
    num_cols = ["NACHr500m", "NACHr1500m", "NACHr5000m",
                "NAINr500m", "NAINr1500m", "NAINr5000m",
                "Ta_mean", "LST_mean", "NDVI_mean", "UHI_mean", "Albedo_mean"]
    for col in num_cols:
        if col in segs.columns:
            segs[col] = pd.to_numeric(segs[col], errors="coerce")

    # Filter: keep only segments with thermal data (inside CDMX)
    segs = segs.dropna(subset=["Ta_mean"])
    print(f"  With thermal data: {len(segs)}")

    # If still too many (>100k), subsample by keeping top NAIN percentile
    if len(segs) > 100000:
        # Keep segments with NAIN >= median (most connected half)
        median_nain = segs["NAINr1500m"].median()
        segs = segs[segs["NAINr1500m"] >= median_nain]
        print(f"  Filtered to above-median NAIN: {len(segs)}")

    process_and_save(segs, OUT / "network.geojson", SIMPLIFY_NETWORK)


# ── 3. PRIORITY SITES ────────────────────────────────────────────────────────
def export_priority():
    print("\n[3/3] Priority sites...")

    parts = []

    # Focus hotspot manzanas (5,050)
    try:
        focus = gpd.read_file(MANZANA_GPKG, layer="manzanas_with_syntax_focus_HS")
        keep = ["CVEGEO", "NOM_MUN", "Ta_mean", "typology_sm_final",
                "peligro_cat", "is_hotspot", "hot_cat_manz",
                "NAINr1500m_lenw_mean", "NACHr1500m_lenw_mean",
                "syntax_score", "syntax_rank_pct", "zone_id",
                "hot26_count_social", "geometry"]
        keep = [c for c in keep if c in focus.columns]
        focus = focus[keep]
        focus["ltype"] = "focus"
        parts.append(focus)
        print(f"  Focus manzanas: {len(focus)}")
    except Exception as e:
        print(f"  Warning: {e}")

    # Top manzanas
    try:
        top = gpd.read_file(ZONES_GPKG, layer="syntax_only_TOP_20250816_0042")
        keep = ["CVEGEO", "NOM_MUN", "Ta_mean", "typology_sm_final",
                "syntax_score", "syntax_rank_pct", "zone_id", "geometry"]
        keep = [c for c in keep if c in top.columns]
        top = top[keep]
        top["ltype"] = "top"
        parts.append(top)
        print(f"  Top manzanas: {len(top)}")
    except Exception as e:
        print(f"  Warning: {e}")

    # 30 zones
    try:
        zones = gpd.read_file(ZONES_GPKG, layer="syntax_only_ZONES_20250816_0042")
        zones["ltype"] = "zone"
        parts.append(zones)
        print(f"  Zones: {len(zones)}")
    except Exception as e:
        print(f"  Warning: {e}")

    if parts:
        combined = pd.concat(parts, ignore_index=True)
        combined = gpd.GeoDataFrame(combined, geometry="geometry")
        if combined.crs is None:
            combined = combined.set_crs(epsg=32614)
        process_and_save(combined, OUT / "priority.geojson", SIMPLIFY_MANZANA)


# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Output: {OUT}")
    print(f"Source: {MANZANA_GPKG}")
    print(f"  exists: {MANZANA_GPKG.exists()}")

    export_manzanas()
    export_network()
    export_priority()

    print("\nDone.")
    total = sum(f.stat().st_size for f in OUT.glob("*.geojson")) / 1e6
    print(f"Total: {total:.1f} MB")
