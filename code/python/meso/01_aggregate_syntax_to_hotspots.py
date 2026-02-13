# -*- coding: utf-8 -*-
"""
Hotspots + Space Matrix (SM v2) + Space Syntax (NACH/NAIN) con peligro
=====================================================================

Objetivo
--------
Caracterizar **manzanas hotspot** (y por tipología SM v2) con **Space Syntax** usando
exclusivamente tus métricas seleccionadas:

- NACHr500m, NACHr1000m, NACHr1500m, NACHr5000m
- NAINr500m, NAINr1000m, NAINr1500m, NAINr5000m

Además, los **segmentos** traen `peligro_cat` (1 = peligro, 2 = peligro extremo).
El script agrega a cada **manzana**:
- Promedio **ponderado por longitud** (y p90) de cada métrica SS dentro de la manzana.
- Lo mismo **por categoría de peligro** del segmento (`*_p1_lenw_mean`, `*_p2_lenw_mean`).
- **Participación de la longitud** de calle en peligro 1 y 2 dentro de la manzana (`len_share_p1`, `len_share_p2`).
- Clasifica peligro de manzana a partir de hotspots: `hot_cat_manz` (=2 si `hot28_any_social`=1; =1 si `hot26_any_social`=1; =0 en otro caso).

Entradas (ajusta rutas si hace falta)
------------------------------------
- MANZ_GPKG  = "/Users/.../01_Manzana/manzanas_thermal_GWR_spacematrix_hotspots_final.gpkg"
- MANZ_LAYER = "manzanas_typology_SM_v2" (se auto-detecta si no existe)
- SEG_GPKG   = "/Users/.../street_network/segmentos_con_termico.gpkg"
- SEG_LAYER  = "segments"

Salidas
-------
- Nuevo layer en el GPKG de manzanas: **`manzanas_with_syntax_focus`**
- CSV espejo: `*_with_syntax_focus.csv`
- Resúmenes:
  - `syntax_focus_hotcat_tipologia.csv` (por hot_cat_manz × tipología SM)
  - `syntax_focus_alcaldia.csv` (por alcaldía)
  - `syntax_focus_QA.csv` (chequeos básicos)

Requisitos: geopandas, shapely (>=2), rtree (opcional), pandas, numpy.
"""
from __future__ import annotations
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import geopandas as gpd

# ======================= RUTAS ===============================================
MANZ_GPKG  = Path("/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/manzanas_thermal_GWR_spacematrix_hotspots_final.gpkg")
MANZ_LAYER = "manzanas_typology_SM_v2"

SEG_GPKG   = Path("/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/street_network/segmentos_con_termico.gpkg")
SEG_LAYER  = "segments"

OUT_LAYER_BASE  = "manzanas_with_syntax_focus"  # nombre base del layer; si filtras hotspots se le añade _HS
NEAR_M     = 40.0     # rescate nearest si no hay intersección
CHUNK      = 12000    # tamaño de lote para intersecciones
EDGE_BUFFER_M = 15.0  # NUEVO: buffer (m) alrededor de cada manzana para captar calles adyacentes
PROCESS_ONLY_HOTSPOTS = True  # NUEVO: procesa SOLO manzanas hotspot para aligerar cómputo y tamaño

# ======================= MÉTRICAS SELECCIONADAS ==============================
SS_METRICS = [
    "NACHr500m","NACHr1000m","NACHr1500m","NACHr5000m",
    "NAINr500m","NAINr1000m","NAINr1500m","NAINr5000m",
]

# ======================= HELPERS =============================================
def _list_layers(gpkg: Path):
    try:
        import fiona
        return fiona.listlayers(gpkg)
    except Exception:
        from pyogrio import list_layers
        return list_layers(gpkg)

def _ensure_manz_layer(gpkg: Path, preferred: str) -> str:
    layers = _list_layers(gpkg)
    if preferred in layers:
        return preferred
    for ly in layers:
        try:
            g = gpd.read_file(gpkg, layer=ly, rows=slice(0, 3), ignore_geometry=True)
            if any("typology_code" in c.lower() for c in g.columns):
                return ly
        except Exception:
            pass
    return layers[0]

def _length_weighted(df: pd.DataFrame, val_cols: list[str], wcol: str) -> pd.Series:
    w = pd.to_numeric(df[wcol], errors="coerce").astype(float)
    w = w.where(w>0, np.nan)
    out = {"street_len_in_manz_m": float(w.sum(skipna=True)) if w.notna().any() else 0.0}
    for c in val_cols:
        x = pd.to_numeric(df.get(c, np.nan), errors="coerce")
        out[f"{c}_lenw_mean"] = (np.average(x[w.notna()], weights=w[w.notna()]) if w.notna().any() else np.nan)
        out[f"{c}_p90"]       = (float(x.quantile(0.90)) if x.notna().any() else np.nan)
    return pd.Series(out)

def _length_weighted_by_peligro(df: pd.DataFrame, val_cols: list[str], wcol: str, pel_col: str) -> pd.Series:
    out = {}
    # shares de longitud por peligro
    w = pd.to_numeric(df[wcol], errors="coerce").astype(float)
    p = pd.to_numeric(df[pel_col], errors="coerce").astype('Int64')
    w_tot = float(w.sum(skipna=True)) if w.notna().any() else 0.0
    for k in (1,2):
        wk = w.where(p==k)
        share = float(wk.sum(skipna=True)/w_tot) if w_tot>0 else 0.0
        out[f"len_share_p{k}"] = share
        for c in val_cols:
            x = pd.to_numeric(df.get(c, np.nan), errors="coerce")
            mask = wk.notna()
            out[f"{c}_p{k}_lenw_mean"] = (np.average(x[mask], weights=wk[mask]) if mask.any() else np.nan)
    return pd.Series(out)

def _agg_segments_to_manz(seg: gpd.GeoDataFrame, manz: gpd.GeoDataFrame, metrics: list[str], pel_col: str="peligro_cat") -> pd.DataFrame:
    """Intersecta segmentos con manzanas (con BUFFER opcional) y agrega por longitud.
    Usa EDGE_BUFFER_M metros alrededor de cada manzana para captar calles adyacentes.
    """
    # CRS métrico razonable
    try:
        crs_metric = manz.estimate_utm_crs() or manz.crs
    except Exception:
        crs_metric = manz.crs
    segm = seg.to_crs(crs_metric)
    mzn  = manz.to_crs(crs_metric)

    # --- NUEVO: buffer de las manzanas para captar calles pegadas al borde ---
    mzb = mzn.copy()
    if EDGE_BUFFER_M and EDGE_BUFFER_M > 0:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mzb["geometry"] = mzb.geometry.buffer(EDGE_BUFFER_M)

    # sjoin candidatos sobre la manzana bufferizada
    keep_cols = [c for c in metrics if c in segm.columns]
    use_cols = ["geometry"] + keep_cols + ([pel_col] if pel_col in segm.columns else [])
    cand = gpd.sjoin(segm[use_cols], mzb[["manzana_id","geometry"]], how="inner", predicate="intersects").reset_index(drop=True)

    # longitud recortada dentro del buffer de manzana (robusto en longitudes)
    cand["_len_m"] = 0.0
    col_idx = cand.columns.get_loc("_len_m")
    for i in range(0, len(cand), CHUNK):
        j = min(i+CHUNK, len(cand))
        sub = cand.iloc[i:j]
        polys = mzb.loc[sub["index_right"], "geometry"].to_numpy()
        lines = sub.geometry.to_numpy()
        inter = [ln.intersection(pl) for ln, pl in zip(lines, polys)]
        lengths = np.array([g.length if (g is not None and not g.is_empty) else 0.0 for g in inter], dtype=float)
        if lengths.shape[0] != (j - i):
            raise RuntimeError(f"Chunk length mismatch: got {lengths.shape[0]} vs {(j-i)}")
        # Asignación POSICIONAL para evitar problemas con índices duplicados
        cand.iloc[i:j, col_idx] = lengths

    cand = cand[cand["_len_m"]>0].copy()

    # Agregación por manzana
    def reducer(g):
        base = _length_weighted(g, keep_cols, "_len_m")
        if pel_col in g.columns:
            byp  = _length_weighted_by_peligro(g, keep_cols, "_len_m", pel_col)
            return pd.concat([base, byp])
        return base

    # Agregación por manzana (evita usar iloc con índices no secuenciales)
    grp = cand.groupby("index_right", group_keys=False)
    try:
        agg = grp.apply(reducer, include_groups=False)  # pandas ≥2.2
    except TypeError:
        agg = grp.apply(reducer)  # compatibilidad pandas <2.2
    # Mapear index_right → manzana_id usando .loc (mismos labels que en mzn)
    agg.index.name = "index_right"
    agg = agg.reset_index()
    agg["manzana_id"] = mzn.loc[agg["index_right"], "manzana_id"].values
    agg = agg.drop(columns="index_right")
    return agg

def _nearest_rescue(seg: gpd.GeoDataFrame, manz: gpd.GeoDataFrame, metrics: list[str], near_m=NEAR_M, pel_col: str="peligro_cat") -> pd.DataFrame:
    try:
        crs_metric = manz.estimate_utm_crs() or manz.crs
    except Exception:
        crs_metric = manz.crs
    segm = seg.to_crs(crs_metric)
    mzn  = manz.to_crs(crs_metric)

    mzc = mzn.copy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mzc["geometry"] = mzc.geometry.centroid

    keep_cols = [c for c in metrics if c in segm.columns]
    use_cols  = ["geometry"] + keep_cols + ([pel_col] if pel_col in segm.columns else [])
    j = gpd.sjoin_nearest(mzc[["manzana_id","geometry"]], segm[use_cols], how="left",
                          max_distance=near_m, distance_col="_dist")
    # renombrar
    ren = {c: f"{c}_near" for c in keep_cols}
    if pel_col in j.columns:
        ren[pel_col] = f"{pel_col}_near"
    out = j[["manzana_id"] + [c for c in ren] + ["_dist"]].rename(columns=ren)
    return out

# ======================= MAIN ===============================================
if __name__ == "__main__":
    print("→ Leyendo manzanas y segmentos…")
    # Manzanas
    manz_layer = _ensure_manz_layer(MANZ_GPKG, MANZ_LAYER)
    manz = gpd.read_file(MANZ_GPKG, layer=manz_layer)
    if "manzana_id" not in manz.columns:
        manz = manz.reset_index(drop=False).rename(columns={"index":"manzana_id"})

    # Campos clave manzana
    def _find(colnames, cands):
        low = [c.lower() for c in colnames]
        for cand in cands:
            if cand.lower() in low:
                return colnames[low.index(cand.lower())]
        for c in colnames:
            if any(cand.lower() in c.lower() for cand in cands):
                return c
        return None

    cols = manz.columns.tolist()
    col_hot26 = _find(cols,["hot26_any_social"]) or "hot26_any_social"
    col_hot28 = _find(cols,["hot28_any_social"]) or "hot28_any_social"
    col_code  = _find(cols,["typology_code_final","typology_code"]) or "typology_code_final"
    col_name  = _find(cols,["typology_sm_final","typology_sm"]) or "typology_sm_final"
    col_alc   = _find(cols,["NOM_MUN","alcaldia","MUN_NAME","NOMGEO","MUN"]) or "NOM_MUN"

    for c in [col_hot26,col_hot28]:
        if c in manz.columns:
            manz[c] = pd.to_numeric(manz[c], errors="coerce").fillna(0).astype(int)
        else:
            manz[c] = 0

    # Segmentos
    seg = gpd.read_file(SEG_GPKG, layer=SEG_LAYER)
    # geoms en 'geom' → estandariza
    if "geometry" not in seg.columns and "geom" in seg.columns:
        seg = gpd.GeoDataFrame(seg, geometry="geom", crs=seg.crs)

    # Enforce numeric on selected metrics (por si vienen como string)
    for c in SS_METRICS:
        if c in seg.columns:
            seg[c] = pd.to_numeric(seg[c], errors="coerce")

    # ================== AGREGACIÓN SEG→MANZ ==================================
    # Filtrar a hotspots si se pide
    if PROCESS_ONLY_HOTSPOTS:
        hot_mask = (manz[col_hot26] == 1) | (manz[col_hot28] == 1)
        manz_proc = manz.loc[hot_mask].copy()
        print(f"→ Procesando SOLO hotspots: {manz_proc.shape[0]} manzanas")
    else:
        manz_proc = manz
        print(f"→ Procesando TODAS las manzanas: {manz_proc.shape[0]}")

    print("→ Intersección segmentos∩manzana + agregación por longitud (y por peligro)…")
    agg = _agg_segments_to_manz(seg, manz_proc, SS_METRICS, pel_col="peligro_cat")

    # Rescate nearest si hace falta
    miss_ids = set(manz_proc["manzana_id"]) - set(agg["manzana_id"])
    if miss_ids:
        print(f"   · Rescate nearest ≤{NEAR_M} m para {len(miss_ids)} manzanas…")
        near = _nearest_rescue(seg, manz_proc.loc[manz_proc["manzana_id"].isin(miss_ids)], SS_METRICS, near_m=NEAR_M, pel_col="peligro_cat")
    else:
        near = pd.DataFrame({"manzana_id":[],"_dist":[]})

    manz2 = manz_proc.merge(agg, on="manzana_id", how="left")
    if not near.empty:
        manz2 = manz2.merge(near, on="manzana_id", how="left")

    # ================== FLAGS Y DERIVADAS ====================================
    # Hot category a nivel manzana (mapeo directo de los flags hotspot)
    manz2["hot_cat_manz"] = np.where(manz2[col_hot28]==1, 2, np.where(manz2[col_hot26]==1, 1, 0)).astype(int)
    manz2["is_hotspot"]   = (manz2["hot_cat_manz"]>0).astype(int)

    # ================== RESÚMENES ===========================================
    # Columnas agregadas efectivas (lenw_mean / p90 / shares)
    agg_cols = [c for c in manz2.columns if c.endswith(('_lenw_mean','_p90')) or c in ("len_share_p1","len_share_p2","street_len_in_manz_m")]

    def _robust_summary(df_in: pd.DataFrame, cols: list[str]) -> pd.Series:
        out = {"n": int(df_in.shape[0])}
        for c in cols:
            x = pd.to_numeric(df_in[c], errors="coerce")
            if x.notna().sum()==0:
                out[f"{c}__med"] = np.nan
                out[f"{c}__p10"] = np.nan
                out[f"{c}__p90"] = np.nan
            else:
                out[f"{c}__med"] = float(x.median())
                out[f"{c}__p10"] = float(x.quantile(0.10))
                out[f"{c}__p90"] = float(x.quantile(0.90))
        return pd.Series(out)

    summary_ht = (manz2.groupby(["hot_cat_manz", col_code, col_name])
                        .apply(lambda d: _robust_summary(d, agg_cols))
                        .reset_index())

    summary_alc = (manz2.groupby(col_alc)
                        .apply(lambda d: _robust_summary(d, agg_cols))
                        .reset_index())

    # ================== QA BÁSICO ============================================
    qa_rows = []
    if ("B_m2" in manz2.columns) and ("A_m2" in manz2.columns):
        viol = int((pd.to_numeric(manz2["B_m2"], errors="coerce") > pd.to_numeric(manz2["A_m2"], errors="coerce")).sum())
        qa_rows.append({"check":"B_m2<=A_m2_violations","value": viol})
    qa_df = pd.DataFrame(qa_rows)

    # ================== SALIDAS ==============================================
    print("→ Escribiendo outputs…")
    OUT_LAYER = OUT_LAYER_BASE + ("_HS" if PROCESS_ONLY_HOTSPOTS else "")
    manz2.to_file(MANZ_GPKG, layer=OUT_LAYER, driver="GPKG")
    csv_out = MANZ_GPKG.with_name(MANZ_GPKG.stem + ("_with_syntax_focus_HS.csv" if PROCESS_ONLY_HOTSPOTS else "_with_syntax_focus.csv"))
    manz2.drop(columns="geometry").to_csv(csv_out, index=False)

    base_dir = MANZ_GPKG.parent
    summary_ht.to_csv(base_dir / "syntax_focus_hotcat_tipologia.csv", index=False)
    summary_alc.to_csv(base_dir / "syntax_focus_alcaldia.csv", index=False)
    qa_df.to_csv(base_dir / "syntax_focus_QA.csv", index=False)

    print("Listo ✅  → Nuevo layer:", OUT_LAYER)
    print("Métricas incluidas:", SS_METRICS)
    print("Resúmenes: syntax_focus_hotcat_tipologia.csv | syntax_focus_alcaldia.csv | syntax_focus_QA.csv")
