# -*- coding: utf-8 -*-
"""
Une variables térmico-sociales (CSV) a manzanas (GPKG) por CVEGEO,
elimina columnas indicadas, y exporta a:
- GPKG + CSV: manzanas_thermal_GWR_spacematrix_hotspots
Capa de entrada en el GPKG: manzanas_v3lite
"""

from pathlib import Path
import pandas as pd
import geopandas as gpd

# ── Entradas ───────────────────────────────────────────────────────────
GPKG_PATH = Path("/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/GWR/GWR_merge/manzanas_master_con_GWR_spacematrix_v3lite_fixBF.gpkg")
CSV_PATH  = Path("/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/manzanas_con_hotspots.csv")

# ── Salidas ────────────────────────────────────────────────────────────
OUT_DIR   = Path("/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana")
OUT_LAYER = "manzanas_thermal_GWR_spacematrix_hotspots_final"
OUT_GPKG  = OUT_DIR / f"{OUT_LAYER}.gpkg"
OUT_CSV   = OUT_DIR / f"{OUT_LAYER}.csv"

# ── Columnas a traer del CSV y a eliminar del GPKG ─────────────────────
COLS_TO_ADD = [
    "is_hot_26","is_hot_28",
    "hot26_pct_65plus","hot28_pct_65plus",
    "hot26_pct_6a14","hot28_pct_6a14",
    "hot26_pct_elementary_edu","hot28_pct_elementary_edu",
    "hot26_pct_inac","hot28_pct_inac",
    "hot26_pct_no_serv_med","hot28_pct_no_serv_med",
    "hot26_pct_pop_sin_auto","hot28_pct_pop_sin_auto",
    "hot26_pct_with_disc","hot28_pct_with_disc",
    "hot26_any_social","hot28_any_social",
    "hot26_count_social","hot28_count_social",
    "peligro_cat"
]
COLS_TO_DROP = [
    "L_niveles","FSI_by_levels","OSR_by_levels",
    "L_diff_equiv_minus_niveles","dq_flag"
]

def norm_cve(s):
    s = s.astype(str).str.strip()
    s = s.str.replace(r"\.0$", "", regex=True)
    return s

def main():
    if not GPKG_PATH.exists():
        raise FileNotFoundError(f"No encuentro el GPKG: {GPKG_PATH}")
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"No encuentro el CSV: {CSV_PATH}")

    # Leer datos
    gdf = gpd.read_file(GPKG_PATH, layer="manzanas_v3lite_fixBF")
    df_hot = pd.read_csv(CSV_PATH)

    # Validar llave
    if "CVEGEO" not in gdf.columns:
        raise ValueError("No encuentro 'CVEGEO' en el GPKG.")
    if "CVEGEO" not in df_hot.columns:
        raise ValueError("No encuentro 'CVEGEO' en el CSV.")

    gdf["CVEGEO"]    = norm_cve(gdf["CVEGEO"])
    df_hot["CVEGEO"] = norm_cve(df_hot["CVEGEO"])

    # Subconjunto de columnas a añadir
    keep_cols = ["CVEGEO"] + [c for c in COLS_TO_ADD if c in df_hot.columns]
    df_hot_sel = df_hot[keep_cols].copy()

    # Merge por CVEGEO
    gdf_out = gdf.merge(df_hot_sel, on="CVEGEO", how="left")

    # Eliminar columnas solicitadas
    drop_present = [c for c in COLS_TO_DROP if c in gdf_out.columns]
    gdf_out = gdf_out.drop(columns=drop_present)

    # Exportar
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    gdf_out.to_file(OUT_GPKG, layer=OUT_LAYER, driver="GPKG")
    gdf_out.drop(columns="geometry").to_csv(OUT_CSV, index=False, encoding="utf-8")

    print(f"✅ Listo.\n→ GPKG: {OUT_GPKG}\n→ CSV : {OUT_CSV}")

if __name__ == "__main__":
    main()
