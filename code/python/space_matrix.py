# -*- coding: utf-8 -*-
"""
Space Matrix v3 LITE — SOLO GPKG (rápido y estable)
Genera por manzana: A, B, F, FSI, GSI, L_equiv, OSR, dq_flag,
n_props, n_predios, area_predios_tot_m2, area_predio_med_m2 (+ QC básico).

Run:
  PYTHONUNBUFFERED=1 python space_matrix_v3_lite.py --out-tag v3lite
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import warnings
warnings.filterwarnings("ignore")

# ───────────────────────────────────────────────────────────────────────────────
# PARÁMETROS
# ───────────────────────────────────────────────────────────────────────────────
CRS_METERS = 32614
MIN_B_AREA_M2 = 10.0      # filtra slivers de huella (B)
MAX_JOIN_DIST = 120       # tolerancia p/ sjoin_nearest puntos→manzana (m)
NEAREST_PREDIOS = 20      # tolerancia para centroids→manzana (m)

# RUTAS
BASE_CITY = Path("/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/Data_catastro/citywide_build")
CITY_GPKG = BASE_CITY / "cdmx_citywide.gpkg"

GWR_DIR   = Path("/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/GWR/GWR_merge")
MANZ_GPKG = GWR_DIR / "manzanas_master_con_GWR.gpkg"

BASE_CAT  = Path("/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/space_matrix/Catastro")
BUILDINGS_GPKG = BASE_CAT / "85d_buildings_filtered.gpkg"
BUILDINGS_LAYER = "85d_buildings_filtered"

# ───────────────────────────────────────────────────────────────────────────────
# HELPERS
# ───────────────────────────────────────────────────────────────────────────────
def clean_buildings(gdf: gpd.GeoDataFrame, min_area=MIN_B_AREA_M2):
    g = gdf.to_crs(CRS_METERS).copy()
    g = g[g.is_valid & g.geometry.notna()]
    g["geometry"] = g.buffer(0)
    g["_area"] = g.area
    g = g[g["_area"] >= float(min_area)].drop(columns=["_area"])
    return g

def join_points_to_manz(points: gpd.GeoDataFrame, manz: gpd.GeoDataFrame, max_dist=MAX_JOIN_DIST):
    """Join puntos→manzana simple con rescate nearest. Devuelve GeoDataFrame con manzana_id."""
    idx = manz[["manzana_id","geometry"]]
    # 1) dentro / covered_by
    try:
        j = gpd.sjoin(points, idx, how="left", predicate="covered_by")
    except Exception:
        j = gpd.sjoin(points, idx, how="left", predicate="within")
    # colapsa a 1 por punto (si se duplicó)
    j_first = j[["manzana_id"]].groupby(level=0).first()
    res = points.join(j_first, how="left")

    # 2) rescate nearest
    miss = res["manzana_id"].isna()
    if miss.any():
        j2 = gpd.sjoin_nearest(points.loc[miss], idx, how="left",
                               max_distance=max_dist, distance_col="dist_m")
        res.loc[j2.index, "manzana_id"] = j2["manzana_id"].values
    return res

def add_mun_ageb(df: pd.DataFrame) -> pd.DataFrame:
    if "CVEGEO" in df.columns:
        cve = df["CVEGEO"].astype(str).str.zfill(16)
        return df.assign(MUN=cve.str[2:5], AGEB=cve.str[9:13])
    return df.assign(MUN="ALL", AGEB="ALL")

def qc_por_mun(df: pd.DataFrame) -> pd.DataFrame:
    d = add_mun_ageb(df.copy())
    falt = ((d["sup_const_tot_m2"]<=0) & (d["B_m2"]>0)).groupby(d["MUN"]).sum()
    tot  = d.groupby("MUN").size()
    npr  = d.groupby("MUN")["n_props"].sum(min_count=1)
    Ftot = d.groupby("MUN")["sup_const_tot_m2"].sum(min_count=1)
    Btot = d.groupby("MUN")["B_m2"].sum(min_count=1)
    qc = pd.DataFrame({"faltantes":falt, "total":tot, "n_props_total":npr, "F_total":Ftot, "B_total":Btot}).fillna(0)
    qc["pct_faltante"] = 100*qc["faltantes"]/qc["total"].replace(0, np.nan)
    return qc.sort_values(["faltantes","pct_faltante"], ascending=False)

# ───────────────────────────────────────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-tag", default="v3lite", help="Sufijo para archivos/layer de salida")
    args = ap.parse_args()

    OUT_GPKG  = GWR_DIR / f"manzanas_master_con_GWR_spacematrix_{args.out_tag}.gpkg"
    OUT_LAYER = f"manzanas_{args.out_tag}"
    OUT_CSV   = GWR_DIR / f"manzanas_master_con_GWR_spacematrix_{args.out_tag}.csv"

    # 1) MANZANAS + A
    print("Cargando manzanas…", flush=True)
    manz = gpd.read_file(MANZ_GPKG).to_crs(CRS_METERS)
    if "manzana_id" not in manz.columns:
        manz = manz.reset_index(drop=False).rename(columns={"index":"manzana_id"})
    manz["A_m2"] = manz.geometry.area

    # 2) B (huellas) — overlay preciso pero único
    print("Cargando footprints de edificios…", flush=True)
    build_raw = gpd.read_file(BUILDINGS_GPKG, layer=BUILDINGS_LAYER)
    build = clean_buildings(build_raw)

    print("Intersecciones exactas (overlay) edificios ∩ manzana…", flush=True)
    bld = build[["geometry"]].reset_index().rename(columns={"index":"b_idx"})
    cand = gpd.sjoin(bld, manz[["manzana_id","geometry"]], how="inner", predicate="intersects")
    g_bld = gpd.GeoDataFrame(cand[["manzana_id","geometry"]].rename(columns={"manzana_id":"mnz_id"}), crs=CRS_METERS)
    g_mnz = gpd.GeoDataFrame(manz[["manzana_id","geometry"]], crs=CRS_METERS)
    inter = gpd.overlay(g_bld, g_mnz, how="intersection")
    inter["area_inter"] = inter.geometry.area
    B_by_manz = inter.groupby("manzana_id")["area_inter"].sum().rename("B_m2")
    manz = manz.merge(B_by_manz, on="manzana_id", how="left").fillna({"B_m2":0.0})
    print(f"✔ B listo (B>0 en {manz['B_m2'].gt(0).sum()} manzanas)", flush=True)

    # 3) F desde catastro_puntos (GPKG)
    print("Cargando catastro_puntos…", flush=True)
    cat = gpd.read_file(CITY_GPKG, layer="catastro_puntos").to_crs(CRS_METERS)
    # normaliza nombres si vienen como sup_const_tot_m2 / sup_terreno_tot_m2
    if "superficie_construccion" not in cat.columns and "sup_const_tot_m2" in cat.columns:
        cat = cat.rename(columns={"sup_const_tot_m2":"superficie_construccion"})
    if "superficie_terreno" not in cat.columns and "sup_terreno_tot_m2" in cat.columns:
        cat = cat.rename(columns={"sup_terreno_tot_m2":"superficie_terreno"})
    for c in ["superficie_construccion","superficie_terreno"]:
        if c not in cat.columns: cat[c] = np.nan
        cat[c] = pd.to_numeric(cat[c], errors="coerce")

    print("Join Catastro → manzana…", flush=True)
    join_p = join_points_to_manz(cat[["geometry","superficie_construccion","superficie_terreno"]], manz, max_dist=MAX_JOIN_DIST)
    F_by_manz  = join_p["superficie_construccion"].groupby(join_p["manzana_id"]).sum(min_count=1).rename("sup_const_tot_m2")
    Terr_by_m  = join_p["superficie_terreno"].groupby(join_p["manzana_id"]).sum(min_count=1).rename("sup_terreno_tot_m2")
    n_props    = join_p.groupby("manzana_id").size().rename("n_props")
    manz = manz.merge(F_by_manz, on="manzana_id", how="left")
    manz = manz.merge(Terr_by_m, on="manzana_id", how="left")
    manz = manz.merge(n_props,   on="manzana_id", how="left")
    manz["sup_const_tot_m2"]   = manz["sup_const_tot_m2"].fillna(0.0)
    manz["sup_terreno_tot_m2"] = manz["sup_terreno_tot_m2"].fillna(0.0)
    manz["n_props"]            = manz["n_props"].fillna(0).astype(int)
    print(f"✔ F listo (F>0 en {manz['sup_const_tot_m2'].gt(0).sum()} manzanas, n_props={int(manz['n_props'].sum())})", flush=True)

    # 4) PREDIOS (rápido): conteo con predios_centroides y áreas con centroides de 'predios'
    print("Cargando predios_centroides para conteo…", flush=True)
    try:
        g_cent = gpd.read_file(CITY_GPKG, layer="predios_centroides").to_crs(CRS_METERS)
    except Exception:
        g_cent = gpd.GeoDataFrame(columns=["geometry"], crs=CRS_METERS)
    if not g_cent.empty:
        jcnt = join_points_to_manz(g_cent[["geometry"]], manz, max_dist=NEAREST_PREDIOS)
        n_predios_by_m = jcnt.groupby("manzana_id").size().rename("n_predios")
        manz = manz.merge(n_predios_by_m, on="manzana_id", how="left")
    else:
        manz["n_predios"] = pd.NA

    print("Cargando predios (polígonos) solo para áreas…", flush=True)
    try:
        g_pred = gpd.read_file(CITY_GPKG, layer="predios").to_crs(CRS_METERS)
    except Exception:
        g_pred = gpd.GeoDataFrame(columns=["geometry"], crs=CRS_METERS)
    if not g_pred.empty:
        g_pred = g_pred[g_pred.geometry.notna() & g_pred.is_valid].copy()
        g_pred["area_predio"] = g_pred.geometry.area
        # asigna por CENTROIDE → manzana (rápido)
        gc = g_pred.copy()
        gc["geometry"] = gc.geometry.centroid
        jarea = join_points_to_manz(gc[["geometry","area_predio"]], manz, max_dist=NEAREST_PREDIOS)
        area_predios_tot = jarea.groupby("manzana_id")["area_predio"].sum(min_count=1).rename("area_predios_tot_m2")
        manz = manz.merge(area_predios_tot, on="manzana_id", how="left")
        # promedio si tenemos conteo:
        if "n_predios" in manz.columns:
            manz["area_predio_med_m2"] = (manz["area_predios_tot_m2"] / manz["n_predios"]).astype(float)
        else:
            manz["area_predio_med_m2"] = np.nan
    else:
        manz["area_predios_tot_m2"] = pd.NA
        manz["area_predio_med_m2"]  = pd.NA

    # 5) INDICADORES (sin niveles normativos en LITE)
    manz["FSI"] = (manz["sup_const_tot_m2"] / manz["A_m2"]).replace([np.inf,-np.inf], np.nan)
    manz["GSI"] = (manz["B_m2"] / manz["A_m2"]).replace([np.inf,-np.inf], np.nan)
    manz["L_equiv"] = np.where((manz["B_m2"]>0), manz["sup_const_tot_m2"] / manz["B_m2"], np.nan)
    manz.loc[manz["FSI"] < 0, "FSI"] = np.nan
    manz.loc[(manz["GSI"] < 0) | (manz["GSI"] > 1), "GSI"] = np.nan
    manz["OSR"] = np.where((manz["FSI"]>0) & manz["GSI"].notna(), (1 - manz["GSI"]) / manz["FSI"], np.nan)

    # Campos by_levels en NA (LITE)
    manz["L_niveles"] = np.nan
    manz["FSI_by_levels"] = np.nan
    manz["OSR_by_levels"] = np.nan
    manz["L_diff_equiv_minus_niveles"] = np.nan

    # 6) FLAGS + QC
    manz["dq_flag"] = 0
    manz.loc[(manz["sup_const_tot_m2"]<=0) & (manz["B_m2"]>0), "dq_flag"] = 1
    manz.loc[(manz["sup_const_tot_m2"]>0) & (manz["B_m2"]<=0), "dq_flag"] = 2
    manz.loc[(manz["sup_const_tot_m2"]<=0) & (manz["B_m2"]<=0), "dq_flag"] = 3

    qc = qc_por_mun(manz.drop(columns="geometry", errors="ignore"))
    qc.to_csv(GWR_DIR / f"qc_por_mun_{args.out_tag}.csv", index=True)

    # 7) EXPORTAR
    print(f"→ Escribiendo {OUT_GPKG.name} (layer {OUT_LAYER})", flush=True)
    manz.to_file(OUT_GPKG, layer=OUT_LAYER, driver="GPKG")
    print(f"→ Escribiendo {OUT_CSV.name}", flush=True)
    manz.drop(columns="geometry").to_csv(OUT_CSV, index=False)
    print("Listo ✅  (LITE: B, F, OSR, conteo/áreas de predios + QC)", flush=True)
