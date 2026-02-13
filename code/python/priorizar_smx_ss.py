# -*- coding: utf-8 -*-
"""
Priorizar áreas de estudio combinando Space Matrix (tipologías) + Space Syntax (500m/1500m)
=========================================================================================

Lógica (alineada a lo acordado):
1) **Ranking de tipologías por severidad de hotspot (hot_cat_manz)**: para *todas* las tipologías, calcular proporciones de manzanas con `hot_cat_manz=2` (peligro extremo) y `=1` (peligro). Construir un **índice de severidad**: `heat_index = HOT_WEIGHT_2·pct_hot2 + HOT_WEIGHT_1·pct_hot1`. Ordenar por `heat_index` y quedarse con **TOP_TYPO_K** tipologías más "calientes" (aplicando `MIN_N_TYPO`).
2) **Priorización por movilidad dentro de esas tipologías**: en las manzanas de esas tipologías **que son hotspot (hot_cat_manz>0)**, construir `mob_500 = z(NAINr500m) + z(NACHr500m)` y `mob_1500 = z(NAINr1500m) + z(NACHr1500m)`. Seleccionar las manzanas que estén simultáneamente en el **top TOP_FRAC** (p.ej. 20%) en `mob_500` y `mob_1500`. Puntuación final: `priority_score = 2*mob_500 + 1*mob_1500 + z(len_share_p2)`.
3) **Salida**: Top-N por tipología y ranking global, en GPKG y CSV.

Entradas
--------
GPKG = "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/analisis_final_tipologias.gpkg"
- La capa se auto-detecta (busca columnas de tipología).
- Debe contener: `typology_code_final`, `typology_sm_final`, `hot_cat_manz`,
  `len_share_p2`, `NAINr500m_lenw_mean`, `NACHr500m_lenw_mean`, `NAINr1500m_lenw_mean`, `NACHr1500m_lenw_mean`.

Salidas
-------
- **Nuevo GPKG** por corrida: `analisis_final_tipologias_prioridad_YYYYMMDD_HHMM.gpkg` (sin mezclar con el original).
- **Nombre de capa** con sello de tiempo: `prioridad_SMxSS_YYYYMMDD_HHMM`.
- **CSVs** con el mismo sello: `…_prioridad_YYYYMMDD_HHMM_manzanas.csv`, `…_prioridad_YYYYMMDD_HHMM_tipologias_hotcat_rank.csv`, `…_prioridad_YYYYMMDD_HHMM_thresholds.csv`, `…_prioridad_YYYYMMDD_HHMM_candidatas_global.csv`.

Ajustes rápidos
---------------
- Cambia parámetros en la sección **PARAMS** de abajo.
---------------
- Cambia parámetros en la sección **PARAMS** de abajo.
-------
- Capa GPKG: `prioridad_SMxSS` (o `prioridad_SMxSS_HS` si filtras a hotspots).
- CSVs: `prioridad_man_zonas.csv`, `prioridad_tipologias_heat_rank.csv`, `prioridad_thresholds.csv`.

Ajustes rápidos
---------------
- Cambia parámetros en la sección **PARAMS** de abajo.
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import geopandas as gpd

# =============== PARAMS ======================================================
INPUT_GPKG = Path("/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/analisis_final_tipologias.gpkg")
PREFERRED_LAYER = None  # si sabes el nombre exacto, ponlo aquí; si no, autodetección

# ¿Procesar solo hotspots? (True/False)
PROCESS_ONLY_HOTSPOTS = False

# Umbrales/controles
MIN_N_TYPO = 30           # mínimo de manzanas por tipología para incluirla en el ranking de paso 1
TOP_TYPO_K = 5            # número de tipologías "más calientes" que pasan a la fase 2
TOP_FRAC_500   = 0.20     # percentil para 500 m (ej. 0.20 = top 20%)
TOP_FRAC_1500  = 0.20     # percentil para 1500 m
TOP_N_PER_TYPO = 20       # número de manzanas finales por tipología
# Pesos para el índice por hot_cat_manz (paso 1)
HOT_WEIGHT_2 = 2.0        # peso de la proporción con hot_cat_manz=2
HOT_WEIGHT_1 = 1.0        # peso de la proporción con hot_cat_manz=1

# Modos de selección de candidatas (UMEP)
#  - STRICT_AND: deben estar en top 500 **y** top 1500
#  - BROAD_OR: deben estar en top 500 **o** top 1500
#  - FIVEHUNDRED_ONLY: solo top 500 (escala peatonal)
#  - HEAT_POCKET: alta exposición térmica (len_share_p2) y al menos top 50% en 500
SELECTION_MODES = ["STRICT_AND", "BROAD_OR", "FIVEHUNDRED_ONLY", "HEAT_POCKET"]

# Balance territorial: cuota por alcaldía (para evitar concentración)
APPLY_ALC_QUOTA = True
QUOTA_PER_ALC = 40        # máximo por alcaldía y por modo

# Unión final para UMEP (una sola capa consolidada)
UNION_MODES = ["FIVEHUNDRED_ONLY", "BROAD_OR", "HEAT_POCKET"]  # modos que se unen
UNION_QUOTA_PER_ALC = 120     # tope por alcaldía en la unión
MAX_PER_TYP_PER_ALC = 20      # tope por tipología dentro de cada alcaldía en la unión

# Escritura
OUT_LAYER_NAME = "prioridad_SMxSS"
WRITE_TO_NEW_GPKG = True  # True -> escribe SIEMPRE a un GPKG nuevo con sello de tiempo  # True -> escribe a *_prioridad.gpkg

# =============== HELPERS =====================================================

def list_layers_safe(gpkg: Path):
    try:
        import fiona
        return fiona.listlayers(gpkg)
    except Exception:
        from pyogrio import list_layers
        return list_layers(gpkg)

def pick_layer_by_columns(gpkg: Path, prefer: str | None = None):
    layers = list_layers_safe(gpkg)
    if prefer and prefer in layers:
        return prefer
    # busca una capa que tenga columnas de tipología
    for ly in layers:
        try:
            g = gpd.read_file(gpkg, layer=ly, rows=slice(0, 5), ignore_geometry=True)
            cols = [c.lower() for c in g.columns]
            if any("typology_code" in c for c in cols) or any("typology_sm" in c for c in cols):
                return ly
        except Exception:
            continue
    return layers[0]

def pick_col(cols: list[str], cands: list[str]) -> str | None:
    low = [c.lower() for c in cols]
    for cand in cands:
        if cand.lower() in low:
            return cols[low.index(cand.lower())]
    # fallback contains
    for c in cols:
        for cand in cands:
            if cand.lower() in c.lower():
                return c
    return None

def zscore(s: pd.Series) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce")
    mu = x.mean(skipna=True)
    sd = x.std(skipna=True)
    if not np.isfinite(sd) or sd == 0:
        return pd.Series(np.nan, index=s.index)
    return (x - mu) / sd

def pct_rank(series: pd.Series) -> pd.Series:
    x = pd.to_numeric(series, errors="coerce")
    return 100.0 * x.rank(pct=True, method="average")

def write_layer_safely(gdf: gpd.GeoDataFrame, out_gpkg: Path, layer_name: str) -> Path:
    import fiona
    # quita capa previa si existe en este archivo destino
    try:
        if out_gpkg.exists():
            layers_now = fiona.listlayers(out_gpkg)
            if layer_name in layers_now:
                fiona.remove(out_gpkg, layer=layer_name, driver="GPKG")
    except Exception as e:
        print("⚠️ No pude eliminar capa previa:", e)
    # escribe y verifica
    gdf.to_file(out_gpkg, layer=layer_name, driver="GPKG")
    layers_final = fiona.listlayers(out_gpkg)
    assert layer_name in layers_final, f"No encuentro la capa '{layer_name}' tras escribir."
    print(f"✅ Escrito: {out_gpkg.name} / capa '{layer_name}' ({len(gdf)} filas)")
    return out_gpkg

# =============== MAIN ========================================================
if __name__ == "__main__":
    print("→ Cargando capa…")
    layer = pick_layer_by_columns(INPUT_GPKG, PREFERRED_LAYER)
    print("   capa:", layer)
    gdf = gpd.read_file(INPUT_GPKG, layer=layer)
    geom_col = gdf.geometry.name  # nombre real de la columna de geometría

    cols = gdf.columns.tolist()
    # columnas clave
    col_typ_c = pick_col(cols, ["typology_code_final","typology_code"]) or "typology_code_final"
    col_typ_n = pick_col(cols, ["typology_sm_final","typology_sm"]) or "typology_sm_final"
    col_lenp2 = pick_col(cols, ["len_share_p2"]) or "len_share_p2"
    col_id    = pick_col(cols, ["manzana_id","id_manzana","id"]) or "manzana_id"
    col_alc   = pick_col(cols, ["NOM_MUN","alcaldia","MUN_NAME","NOMGEO","MUN"]) or "NOM_MUN"

    col_NAIN_500  = pick_col(cols, ["NAINr500m_lenw_mean"]) or "NAINr500m_lenw_mean"
    col_NACH_500  = pick_col(cols, ["NACHr500m_lenw_mean"]) or "NACHr500m_lenw_mean"
    col_NAIN_1500 = pick_col(cols, ["NAINr1500m_lenw_mean"]) or "NAINr1500m_lenw_mean"
    col_NACH_1500 = pick_col(cols, ["NACHr1500m_lenw_mean"]) or "NACHr1500m_lenw_mean"

    # hotspot opcional
    col_hotcat = pick_col(cols, ["hot_cat_manz"]) or None
    if PROCESS_ONLY_HOTSPOTS and col_hotcat and col_hotcat in gdf.columns:
        gdf = gdf[pd.to_numeric(gdf[col_hotcat], errors="coerce").fillna(0).astype(int) > 0].copy()
        OUT_LAYER = OUT_LAYER_NAME + "_HS"
    else:
        OUT_LAYER = OUT_LAYER_NAME

    # ==== Paso 1: ranking de tipologías por hot_cat_manz =====================
    print("→ Paso 1: ranking de tipologías por hot_cat_manz (proporciones y heat_index)…")
    # columnas/numéricos
    col_hotcat = pick_col(cols, ["hot_cat_manz"]) or "hot_cat_manz"
    gdf[col_hotcat] = pd.to_numeric(gdf[col_hotcat], errors="coerce")

    # conteos por tipología y hot_cat
    grp = gdf.groupby([col_typ_c, col_typ_n])
    n_total = grp.size().rename("n")
    n_hot2  = grp.apply(lambda x: (x[col_hotcat]==2).sum()).rename("n_hot2")
    n_hot1  = grp.apply(lambda x: (x[col_hotcat]==1).sum()).rename("n_hot1")

    typo_grp = pd.concat([n_total, n_hot2, n_hot1], axis=1).reset_index()
    typo_grp["pct_hot2"] = typo_grp["n_hot2"] / typo_grp["n"].replace(0, np.nan)
    typo_grp["pct_hot1"] = typo_grp["n_hot1"] / typo_grp["n"].replace(0, np.nan)
    typo_grp["heat_index"] = HOT_WEIGHT_2*typo_grp["pct_hot2"] + HOT_WEIGHT_1*typo_grp["pct_hot1"]

    # filtrar por mínimo n y ordenar
    typo_grp = typo_grp[typo_grp["n"] >= MIN_N_TYPO].copy()
    typo_rank = typo_grp.sort_values(["heat_index","pct_hot2","n"], ascending=[False, False, False])

    top_typo = typo_rank.head(TOP_TYPO_K)[[col_typ_c, col_typ_n]]
    top_codes = set(top_typo[col_typ_c].astype(str))

# ==== Paso 2: movilidad dentro de esas tipologías ========================
    print("→ Paso 2: priorización por movilidad (500 y 1500) en tipologías Top-K…")
    d = gdf[(gdf[col_typ_c].astype(str).isin(top_codes)) & (pd.to_numeric(gdf.get("hot_cat_manz", 0), errors="coerce")>0)].copy()

    # construir z-scores de movilidad
    for c in [col_NAIN_500, col_NACH_500, col_NAIN_1500, col_NACH_1500]:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")

    d["mob_500"]  = zscore(d[col_NAIN_500]) + zscore(d[col_NACH_500])
    d["mob_1500"] = zscore(d[col_NAIN_1500]) + zscore(d[col_NACH_1500])

    # percentiles (0–100) y umbrales por escala
    d["rank_500_pct"]  = pct_rank(d["mob_500"])   # 0–100
    d["rank_1500_pct"] = pct_rank(d["mob_1500"])  # 0–100
    thr500 = 100.0 * (1.0 - TOP_FRAC_500)   # ej. 80
    thr1500 = 100.0 * (1.0 - TOP_FRAC_1500) # ej. 80

    # prioridad final (doble peso 500m + calor)
    d["priority_score"] = 2.0*d["mob_500"] + 1.0*d["mob_1500"] + zscore(d[col_lenp2])

    # umbral para HEAT_POCKET (tercil superior de exposición)
    heat_q66 = pd.to_numeric(d[col_lenp2], errors="coerce").quantile(0.66)

    # Selecciones por modo
    def select_by_mode(df_in, mode: str):
        if mode == "STRICT_AND":
            m = (df_in["rank_500_pct"] >= thr500) & (df_in["rank_1500_pct"] >= thr1500)
        elif mode == "BROAD_OR":
            m = (df_in["rank_500_pct"] >= thr500) | (df_in["rank_1500_pct"] >= thr1500)
        elif mode == "FIVEHUNDRED_ONLY":
            m = (df_in["rank_500_pct"] >= thr500)
        elif mode == "HEAT_POCKET":
            m = (pd.to_numeric(df_in[col_lenp2], errors="coerce") >= heat_q66) & (df_in["rank_500_pct"] >= 50.0)
        else:
            m = pd.Series(False, index=df_in.index)
        out = df_in[m].copy()
        out["sel_mode"] = mode
        return out

    selections = {m: select_by_mode(d, m) for m in SELECTION_MODES}

    # Balance territorial opcional por alcaldía
    def apply_quota(gdf_in: gpd.GeoDataFrame, group_col: str, quota: int) -> gpd.GeoDataFrame:
        if gdf_in.empty or (group_col not in gdf_in.columns):
            return gdf_in
        gdf_in = gdf_in.sort_values(["priority_score", "rank_500_pct", "rank_1500_pct"], ascending=False)
        parts = []
        for key, sub in gdf_in.groupby(group_col, group_keys=False):
            parts.append(sub.head(quota))
        return gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), geometry=geom_col, crs=gdf_in.crs)

    if APPLY_ALC_QUOTA and col_alc in d.columns:
        for k in list(selections.keys()):
            selections[k] = apply_quota(selections[k], col_alc, QUOTA_PER_ALC)

    d["priority_score"] = 2.0*d["mob_500"] + 1.0*d["mob_1500"] + zscore(d[col_lenp2])

    # ==== Paso 3: selección final ===========================================
    print("→ Paso 3: selección Top-N por tipología y ranking global…")
    # Top-N por tipología (entre las que cumplen modo ESTRICTO)
    strict = selections.get("STRICT_AND", d.iloc[0:0].copy())
    final_rows = []
    for tcode, tname in sorted(top_codes):
        sub = strict[(strict[col_typ_c].astype(str) == tcode)].copy()
        sub = sub.sort_values("priority_score", ascending=False).head(TOP_N_PER_TYPO)
        sub["rank_en_tipologia"] = np.arange(1, len(sub)+1)
        final_rows.append(sub)
    if final_rows:
        final = gpd.GeoDataFrame(pd.concat(final_rows, ignore_index=True), geometry=geom_col, crs=gdf.crs)
    else:
        final = gpd.GeoDataFrame(pd.DataFrame(), geometry=geom_col, crs=gdf.crs)

    # Ranking global de candidatas por cada modo
    cand_modes = {k: v.sort_values("priority_score", ascending=False).reset_index(drop=True) for k, v in selections.items()}
    for k, dfk in cand_modes.items():
        dfk["rank_global"] = np.arange(1, len(dfk)+1)
        cand_modes[k] = gpd.GeoDataFrame(dfk, geometry=geom_col, crs=gdf.crs)

# ==== Escritura ==========================================================
    print("→ Escribiendo resultados…")
    # Sello de tiempo para nombres únicos
    RUN_TAG = datetime.now().strftime("%Y%m%d_%H%M")
    OUT_LAYER_TAGGED = OUT_LAYER + f"_{RUN_TAG}"

    # 1) GPKG nuevo con sello de tiempo
    out_gpkg = INPUT_GPKG.with_name(INPUT_GPKG.stem + f"_prioridad_{RUN_TAG}.gpkg")
    # Escribir SIEMPRE varias capas: FINAL (estricto) y CANDIDATAS por modo
    if not final.empty:
        write_layer_safely(final, out_gpkg, OUT_LAYER_TAGGED)
    else:
        print("⚠️ No hubo Top-N por tipología en modo estricto.")
    for k, dfk in cand_modes.items():
        if not dfk.empty:
            write_layer_safely(dfk, out_gpkg, OUT_LAYER_TAGGED + f"_{k}")

    # 2) Unión UMEP: FIVEHUNDRED_ONLY ∪ BROAD_OR ∪ HEAT_POCKET
    def union_umep(cand_modes: dict) -> gpd.GeoDataFrame:
        parts = [cand_modes[m] for m in UNION_MODES if m in cand_modes and not cand_modes[m].empty]
        if not parts:
            return gpd.GeoDataFrame(pd.DataFrame(), geometry=geom_col, crs=gdf.crs)
        u = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), geometry=geom_col, crs=gdf.crs)
        # ordenar por prioridad y quitar duplicados por manzana (conservar la mejor)
        if col_id in u.columns:
            u = u.sort_values(["priority_score","rank_500_pct","rank_1500_pct"], ascending=False)
            u = u.drop_duplicates(subset=[col_id], keep="first")
        # aplicar límites tipología dentro de alcaldía, y luego cuota por alcaldía
        if col_alc in u.columns and col_typ_c in u.columns:
            blocks = []
            for alc_key, g_alc in u.groupby(col_alc, group_keys=False):
                g_alc = g_alc.sort_values(["priority_score","rank_500_pct","rank_1500_pct"], ascending=False)
                sub_parts = []
                for typ_key, g_typ in g_alc.groupby(col_typ_c, group_keys=False):
                    sub_parts.append(g_typ.head(MAX_PER_TYP_PER_ALC))
                g_pack = pd.concat(sub_parts, ignore_index=True)
                g_pack = g_pack.sort_values(["priority_score","rank_500_pct","rank_1500_pct"], ascending=False).head(UNION_QUOTA_PER_ALC)
                blocks.append(g_pack)
            u2 = gpd.GeoDataFrame(pd.concat(blocks, ignore_index=True), geometry=geom_col, crs=u.crs)
        else:
            u2 = u
        return u2

    umepl = union_umep(cand_modes)
    if not umepl.empty:
        write_layer_safely(umepl, out_gpkg, OUT_LAYER_TAGGED + "_UMEP_CANDIDATAS")
    else:
        print("⚠️ Unión UMEP vacía (revisa umbrales o modos seleccionados).")

    # 3) CSVs con el mismo sello (junto al GPKG nuevo)
    base_dir = out_gpkg.parent
    stem = out_gpkg.stem  # incluye _prioridad_YYYYMMDD_HHMM

    # Selección final Top-N tipología (estricto)
    csv_sel = base_dir / f"{stem}_manzanas_FINAL.csv"
    final.drop(columns=geom_col, errors="ignore").to_csv(csv_sel, index=False)

    # Candidatas por modo (CSV por cada modo)
    for k, dfk in cand_modes.items():
        dfk.drop(columns=geom_col, errors="ignore").to_csv(base_dir / f"{stem}_candidatas_{k}.csv", index=False)

    # Unión UMEP CSV
    if not umepl.empty:
        umepl.drop(columns=geom_col, errors="ignore").to_csv(base_dir / f"{stem}_UMEP_CANDIDATAS.csv", index=False)

    # Ranking de tipologías por hot_cat
    csv_typ = base_dir / f"{stem}_tipologias_hotcat_rank.csv"
    typo_rank.to_csv(csv_typ, index=False)

    # Umbrales usados
    csv_thr = base_dir / f"{stem}_thresholds.csv"
    pd.DataFrame({
        "metric": ["rank_500_pct","rank_1500_pct","len_share_p2_q66"],
        "threshold": [thr500, thr1500, heat_q66],
        "note": [f"TOP_FRAC_500={TOP_FRAC_500}", f"TOP_FRAC_1500={TOP_FRAC_1500}", "HEAT_POCKET usa q66"]
    }).to_csv(csv_thr, index=False)

    print("Listo ✅")
    print("Layer base (estricto):", OUT_LAYER_TAGGED, "en", out_gpkg)
    if not umepl.empty:
        print("Layer consolidada UMEP:", OUT_LAYER_TAGGED + "_UMEP_CANDIDATAS")
    print("CSVs en:", base_dir)
    print("→ Escribiendo resultados…")
    # Sello de tiempo para nombres únicos
    RUN_TAG = datetime.now().strftime("%Y%m%d_%H%M")
    OUT_LAYER_TAGGED = OUT_LAYER + f"_{RUN_TAG}"

    # 1) GPKG nuevo con sello de tiempo
    out_gpkg = INPUT_GPKG.with_name(INPUT_GPKG.stem + f"_prioridad_{RUN_TAG}.gpkg")
    # Escribir SIEMPRE varias capas: FINAL (estricto) y CANDIDATAS por modo
    if not final.empty:
        write_layer_safely(final, out_gpkg, OUT_LAYER_TAGGED)
    else:
        print("⚠️ No hubo Top-N por tipología en modo estricto.")
    for k, dfk in cand_modes.items():
        if not dfk.empty:
            write_layer_safely(dfk, out_gpkg, OUT_LAYER_TAGGED + f"_{k}")

    # 2) CSVs con el mismo sello (junto al GPKG nuevo)
    base_dir = out_gpkg.parent
    stem = out_gpkg.stem  # incluye _prioridad_YYYYMMDD_HHMM

    # Selección final Top-N tipología (estricto)
    csv_sel = base_dir / f"{stem}_manzanas_FINAL.csv"
    final.drop(columns=geom_col, errors="ignore").to_csv(csv_sel, index=False)

    # Candidatas por modo (CSV por cada modo)
    for k, dfk in cand_modes.items():
        dfk.drop(columns=geom_col, errors="ignore").to_csv(base_dir / f"{stem}_candidatas_{k}.csv", index=False)

    # Ranking de tipologías por hot_cat
    csv_typ = base_dir / f"{stem}_tipologias_hotcat_rank.csv"
    typo_rank.to_csv(csv_typ, index=False)

    # Umbrales usados
    csv_thr = base_dir / f"{stem}_thresholds.csv"
    pd.DataFrame({
        "metric": ["rank_500_pct","rank_1500_pct","len_share_p2_q66"],
        "threshold": [thr500, thr1500, heat_q66],
        "note": [f"TOP_FRAC_500={TOP_FRAC_500}", f"TOP_FRAC_1500={TOP_FRAC_1500}", "HEAT_POCKET usa q66"]
    }).to_csv(csv_thr, index=False)

    print("Listo ✅")
    print("Layer base (estricto):", OUT_LAYER_TAGGED, "en", out_gpkg)
    print("CSV selección FINAL:", csv_sel)
    print("CSV tipologías por hot_cat:", csv_typ)
    print("CSV umbrales:", csv_thr)
    print("CSVs candidatas por modo en:", base_dir)
