# -*- coding: utf-8 -*-
"""
Space Matrix v3 LITE — B robusto (unión de huellas) + F fortalecido (rescates)
Fix: manejar columnas duplicadas 'manzana_id' tras overlay con sufijos (_1/_2).
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import warnings
warnings.filterwarnings("ignore")

CRS_METERS = 32614
MIN_B_AREA_M2 = 10.0
MAX_JOIN_DIST = 120
RESCUE_JOIN_DIST = 200
NEAREST_PREDIOS = 20

BASE_CITY = Path("/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/Data_catastro/citywide_build")
CITY_GPKG = BASE_CITY / "cdmx_citywide.gpkg"

GWR_DIR   = Path("/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/GWR/GWR_merge")
MANZ_GPKG = GWR_DIR / "manzanas_master_con_GWR.gpkg"

BASE_CAT  = Path("/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/space_matrix/Catastro")
BUILDINGS_GPKG = BASE_CAT / "85d_buildings_filtered.gpkg"
BUILDINGS_LAYER = "85d_buildings_filtered"

def clean_buildings(gdf: gpd.GeoDataFrame, min_area=MIN_B_AREA_M2):
    g = gdf.to_crs(CRS_METERS).copy()
    g = g[g.geometry.notna() & g.is_valid]
    g["geometry"] = g.buffer(0)
    g["_area"] = g.area
    g = g[g["_area"] >= float(min_area)].drop(columns=["_area"])
    return g

def join_points_to_manz(points: gpd.GeoDataFrame, manz: gpd.GeoDataFrame, max_dist=MAX_JOIN_DIST):
    idx = manz[["manzana_id","geometry"]]
    try:
        j = gpd.sjoin(points, idx, how="left", predicate="covered_by")
    except Exception:
        j = gpd.sjoin(points, idx, how="left", predicate="within")
    j_first = j[["manzana_id"]].groupby(level=0).first()
    res = points.join(j_first, how="left")
    miss = res["manzana_id"].isna()
    if miss.any():
        j2 = gpd.sjoin_nearest(points.loc[miss], idx, how="left",
                               max_distance=max_dist, distance_col="dist_m")
        res.loc[j2.index, "manzana_id"] = j2["manzana_id"].values
    return res

def join_points_to_manz_rescue(points_missing: gpd.GeoDataFrame, manz: gpd.GeoDataFrame, max_dist=RESCUE_JOIN_DIST):
    if points_missing.empty:
        return points_missing.assign(manzana_id=pd.NA)
    idx = manz[["manzana_id","geometry"]]
    j = gpd.sjoin_nearest(points_missing, idx, how="left",
                          max_distance=max_dist, distance_col="dist_m2")
    return j[["manzana_id"]]

def add_mun_ageb(df: pd.DataFrame) -> pd.DataFrame:
    if "CVEGEO" in df.columns:
        cve = df["CVEGEO"].astype(str).str.zfill(16)
        return df.assign(MUN=cve.str[2:5], AGEB=cve.str[9:13])
    return df.assign(MUN="ALL", AGEB="ALL")

def qc_por_mun(df: pd.DataFrame) -> pd.DataFrame:
    d = add_mun_ageb(df.copy())
    falt_1 = ((d["sup_const_tot_m2"]<=0) & (d["B_m2"]>0)).groupby(d["MUN"]).sum()
    falt_2 = ((d["sup_const_tot_m2"]>0) & (d["B_m2"]<=0)).groupby(d["MUN"]).sum()
    falt_3 = ((d["sup_const_tot_m2"]<=0) & (d["B_m2"]<=0)).groupby(d["MUN"]).sum()
    tot  = d.groupby("MUN").size()
    npr  = d.groupby("MUN")["n_props"].sum(min_count=1)
    Ftot = d.groupby("MUN")["sup_const_tot_m2"].sum(min_count=1)
    Btot = d.groupby("MUN")["B_m2"].sum(min_count=1)
    qc = pd.DataFrame({
        "flag1_F<=0_B>0":falt_1, "flag2_F>0_B<=0":falt_2, "flag3_F<=0_B<=0":falt_3,
        "total":tot, "n_props_total":npr, "F_total":Ftot, "B_total":Btot
    }).fillna(0)
    for c in ["flag1_F<=0_B>0","flag2_F>0_B<=0","flag3_F<=0_B<=0"]:
        qc[f"pct_{c}"] = 100*qc[c]/qc["total"].replace(0, np.nan)
    return qc.sort_values("flag1_F<=0_B>0", ascending=False)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-tag", default="v3lite_fixBF", help="Sufijo para archivos/layer de salida")
    args = ap.parse_args()

    OUT_GPKG  = GWR_DIR / f"manzanas_master_con_GWR_spacematrix_{args.out_tag}.gpkg"
    OUT_LAYER = f"manzanas_{args.out_tag}"
    OUT_CSV   = GWR_DIR / f"manzanas_master_con_GWR_spacematrix_{args.out_tag}.csv"

    print("Cargando manzanas…", flush=True)
    manz = gpd.read_file(MANZ_GPKG).to_crs(CRS_METERS)
    if "manzana_id" not in manz.columns:
        manz = manz.reset_index(drop=False).rename(columns={"index":"manzana_id"})
    manz["A_m2"] = manz.geometry.area

    print("Cargando footprints de edificios…", flush=True)
    build_raw = gpd.read_file(BUILDINGS_GPKG, layer=BUILDINGS_LAYER)
    build = clean_buildings(build_raw)

    print("Intersecciones edificios ∩ manzana y UNIÓN por manzana…", flush=True)
    bld = build[["geometry"]].reset_index(drop=True)
    cand = gpd.sjoin(
        gpd.GeoDataFrame(bld, geometry="geometry", crs=CRS_METERS),
        manz[["manzana_id","geometry"]], how="inner", predicate="intersects"
    )[["manzana_id","geometry"]]

    g_bld = gpd.GeoDataFrame(cand, crs=CRS_METERS)
    g_mnz = gpd.GeoDataFrame(manz[["manzana_id","geometry"]], crs=CRS_METERS)
    inter = gpd.overlay(g_bld, g_mnz, how="intersection")

    # ✔ FIX: geopandas.overlay añade sufijos para columnas repetidas.
    # Buscamos cualquier columna 'manzana_id', preferimos la que proviene de manzanas.
    mnz_cols = [c for c in inter.columns if c.lower().startswith('manzana_id')]
    if not mnz_cols:
        raise KeyError("No se encontró 'manzana_id' tras el overlay. Columnas: %s" % list(inter.columns))
    # Preferimos la segunda (sufijo _2) si existe; si no, usamos la primera.
    prefer = [c for c in mnz_cols if c.endswith('_2')]
    use_col = prefer[0] if prefer else mnz_cols[0]
    inter = inter.rename(columns={use_col: 'manzana_id'})[['manzana_id','geometry']]

    # UNIÓN geométrica por manzana (evita doble conteo) y área
    B_union = (inter.groupby("manzana_id")["geometry"]
                     .apply(lambda geoms: geoms.unary_union)
                     .apply(lambda g: g.area if g is not None else 0.0)
                     .rename("B_m2"))

    manz = manz.merge(B_union, on="manzana_id", how="left").fillna({"B_m2":0.0})
    manz["B_m2"] = manz[["B_m2","A_m2"]].min(axis=1)
    print(f"✔ B listo (B>0 en {manz['B_m2'].gt(0).sum()} manzanas)", flush=True)

    print("Cargando catastro_puntos…", flush=True)
    cat = gpd.read_file(CITY_GPKG, layer="catastro_puntos").to_crs(CRS_METERS)

    if "superficie_construccion" not in cat.columns and "sup_const_tot_m2" in cat.columns:
        cat = cat.rename(columns={"sup_const_tot_m2":"superficie_construccion"})
    if "superficie_terreno" not in cat.columns and "sup_terreno_tot_m2" in cat.columns:
        cat = cat.rename(columns={"sup_terreno_tot_m2":"superficie_terreno"})
    for c in ["superficie_construccion","superficie_terreno"]:
        if c not in cat.columns: cat[c] = np.nan
        cat[c] = pd.to_numeric(cat[c], errors="coerce")
        cat.loc[cat[c].eq(0), c] = np.nan

    print("Join Catastro → manzana (paso 1)…", flush=True)
    join_p1 = join_points_to_manz(cat[["geometry","superficie_construccion","superficie_terreno"]], manz, max_dist=MAX_JOIN_DIST)

    miss_idx = join_p1["manzana_id"].isna()
    if miss_idx.any():
        print(f"Rescate Catastro faltantes (paso 2, {RESCUE_JOIN_DIST} m)…", flush=True)
        rescue = join_points_to_manz_rescue(join_p1.loc[miss_idx, ["geometry"]], manz, max_dist=RESCUE_JOIN_DIST)
        join_p1.loc[miss_idx, "manzana_id"] = rescue["manzana_id"].values

    F_by_manz  = join_p1.groupby("manzana_id")["superficie_construccion"].sum(min_count=1).rename("sup_const_tot_m2")
    Terr_by_m  = join_p1.groupby("manzana_id")["superficie_terreno"].sum(min_count=1).rename("sup_terreno_tot_m2")
    n_props    = join_p1.groupby("manzana_id").size().rename("n_props")

    manz = manz.merge(F_by_manz, on="manzana_id", how="left")
    manz = manz.merge(Terr_by_m, on="manzana_id", how="left")
    manz = manz.merge(n_props,   on="manzana_id", how="left")

    manz["sup_const_tot_m2"]   = manz["sup_const_tot_m2"].fillna(0.0)
    manz["sup_terreno_tot_m2"] = manz["sup_terreno_tot_m2"].fillna(0.0)
    manz["n_props"]            = manz["n_props"].fillna(0).astype(int)
    print(f"✔ F listo (F>0 en {manz['sup_const_tot_m2'].gt(0).sum()} manzanas, n_props={int(manz['n_props'].sum())})", flush=True)

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
        gc = g_pred.copy()
        gc["geometry"] = gc.geometry.centroid
        jarea = join_points_to_manz(gc[["geometry","area_predio"]], manz, max_dist=NEAREST_PREDIOS)
        area_predios_tot = jarea.groupby("manzana_id")["area_predio"].sum(min_count=1).rename("area_predios_tot_m2")
        manz = manz.merge(area_predios_tot, on="manzana_id", how="left")
        if "n_predios" in manz.columns:
            manz["area_predio_med_m2"] = (manz["area_predios_tot_m2"] / manz["n_predios"]).astype(float)
        else:
            manz["area_predio_med_m2"] = np.nan
    else:
        manz["area_predios_tot_m2"] = pd.NA
        manz["area_predio_med_m2"]  = pd.NA

    manz["FSI"] = (manz["sup_const_tot_m2"] / manz["A_m2"]).replace([np.inf,-np.inf], np.nan)
    manz["GSI"] = (manz["B_m2"] / manz["A_m2"]).replace([np.inf,-np.inf], np.nan)
    manz["L_equiv"] = np.where((manz["B_m2"]>0), manz["sup_const_tot_m2"] / manz["B_m2"], np.nan)
    manz.loc[manz["FSI"] < 0, "FSI"] = np.nan
    manz.loc[(manz["GSI"] < 0) | (manz["GSI"] > 1), "GSI"] = np.nan
    manz["OSR"] = np.where((manz["FSI"]>0) & manz["GSI"].notna(), (1 - manz["GSI"]) / manz["FSI"], np.nan)

    manz["L_niveles"] = np.nan
    manz["FSI_by_levels"] = np.nan
    manz["OSR_by_levels"] = np.nan
    manz["L_diff_equiv_minus_niveles"] = np.nan

    manz["dq_flag"] = 0
    manz.loc[(manz["sup_const_tot_m2"]<=0) & (manz["B_m2"]>0), "dq_flag"] = 1
    manz.loc[(manz["sup_const_tot_m2"]>0) & (manz["B_m2"]<=0), "dq_flag"] = 2
    manz.loc[(manz["sup_const_tot_m2"]<=0) & (manz["B_m2"]<=0), "dq_flag"] = 3

    qc = qc_por_mun(manz.drop(columns="geometry", errors="ignore"))
    qc_path = GWR_DIR / f"qc_por_mun_{args.out_tag}.csv"
    qc.to_csv(qc_path, index=True)
    print(f"QC por municipio escrito en: {qc_path}", flush=True)

    print(f"→ Escribiendo {OUT_GPKG.name} (layer {OUT_LAYER})", flush=True)
    manz.to_file(OUT_GPKG, layer=OUT_LAYER, driver="GPKG")
    print(f"→ Escribiendo {OUT_CSV.name}", flush=True)
    manz.drop(columns="geometry").to_csv(OUT_CSV, index=False)
    print("Listo ✅  (B por unión, F con rescates y QC)")
