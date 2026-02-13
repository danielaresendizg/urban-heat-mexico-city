# -*- coding: utf-8 -*-
"""
OLS + Moran's I de residuos (CDMX · manzana) — versión final sin 'spreg'
-----------------------------------------------------------------------
- OLS con statsmodels (errores robustos opcionales: white/HC0–HC3)
- Moran's I de residuos con esda/libpysal
- Corre por alcaldía y para toda la ciudad
- Exporta:
    * CSV resumen por alcaldía (R², AIC, Moran’s I/p, etc.)
    * CSV de coeficientes por alcaldía (beta y error estándar)
    * (opcional) GPKG con predicciones y residuos por manzana

Ejemplo:
  python 140824_OLS_Moran_statsmodels.py \
    --gpkg "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/GWR/GWR_merge/manzanas_master_con_GWR_spacematrix_v3lite.gpkg" \
    --layer manzanas_v3lite \
    --outdir "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/GWR/GWR_merge" \
    --xvars pct_pop_sin_auto,pct_no_serv_med,pct_inac,pct_65plus,pct_6a14,pct_with_disc,pct_elementary_edu \
    --weights queen --robust white --save-gpkg
"""

import os
import argparse
from typing import List, Optional, Tuple, Dict

import numpy as np
import pandas as pd
import geopandas as gpd

import statsmodels.api as sm
from libpysal.weights import Queen, KNN
from esda import Moran

# Para listar capas y dar sugerencias si 'layer' no existe
try:
    from pyogrio import list_layers as _list_layers
except Exception:
    _list_layers = None

# ─────────────────────────────────────────────────────────────
# Parámetros por defecto (ajustados a tu estructura)
# ─────────────────────────────────────────────────────────────
DEFAULT_GPKG  = "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/GWR/GWR_merge/manzanas_master_con_GWR_spacematrix_v3lite.gpkg"
DEFAULT_LAYER = "manzanas_v3lite"
DEFAULT_OUT   = "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/GWR/GWR_merge"

VARS_X_BASE = [
    "pct_pop_sin_auto",
    "pct_no_serv_med",
    "pct_inac",
    "pct_65plus",
    "pct_6a14",
    "pct_with_disc",
    "pct_elementary_edu",
]

# ─────────────────────────────────────────────────────────────
# Utils
# ─────────────────────────────────────────────────────────────
def log(msg: str):
    print(msg, flush=True)

def parse_args():
    p = argparse.ArgumentParser(description="OLS + Moran's I por alcaldía y ciudad completa (sin spreg)")
    p.add_argument("--gpkg", default=DEFAULT_GPKG, help="Ruta al GeoPackage de entrada")
    p.add_argument("--layer", default=DEFAULT_LAYER, help="Nombre del layer de manzanas")
    p.add_argument("--outdir", default=DEFAULT_OUT, help="Directorio de salida")
    p.add_argument("--yvar", default="Ta_mean", help="Variable dependiente")
    p.add_argument("--xvars", default=",".join(VARS_X_BASE), help="Lista coma-separada de X (sin constante)")
    p.add_argument("--weights", default="queen", choices=["queen", "knn"], help="Pesos espaciales")
    p.add_argument("--k", type=int, default=8, help="k para KNN (si se usa o como fallback)")
    p.add_argument("--robust", default=None, choices=[None, "white", "hc0", "hc1", "hc2", "hc3"],
                   help="Errores robustos: white (HC0) o HCx; por defecto None")
    p.add_argument("--save-gpkg", action="store_true", help="Guardar GPKG con predicciones/residuos")
    return p.parse_args()

def find_mun_col(df: pd.DataFrame) -> Optional[str]:
    for cand in ["NOM_MUN", "alcaldia", "municipio", "MUN"]:
        if cand in df.columns:
            return cand
    return None

def ensure_projected(gdf: gpd.GeoDataFrame, epsg: str = "EPSG:32614") -> gpd.GeoDataFrame:
    try:
        if gdf.crs is None or gdf.crs.to_string().lower() != epsg.lower():
            return gdf.to_crs(epsg)
        return gdf
    except Exception:
        return gdf.to_crs(epsg)

def build_weights(gdf: gpd.GeoDataFrame, method: str = "queen", k: int = 8):
    """
    method='queen' intenta contigüidad. Si hay islas, cae a KNN(k).
    method='knn' va directo a KNN(k).
    """
    method = method.lower()
    if method == "queen":
        try:
            w = Queen.from_dataframe(gdf, ids=gdf.index)
            if hasattr(w, "islands") and len(w.islands) > 0:
                log(f"⚠️  Queen tiene islas ({len(w.islands)}). Fallback a KNN(k={k}).")
                w = KNN.from_dataframe(gdf, k=k, ids=gdf.index)
        except Exception:
            log("⚠️  Queen falló; usando KNN.")
            w = KNN.from_dataframe(gdf, k=k, ids=gdf.index)
    else:
        w = KNN.from_dataframe(gdf, k=k, ids=gdf.index)
    w.transform = "R"  # estandarización por filas
    return w

def safe_numeric(df: pd.DataFrame, cols: List[str]):
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

def slug(s: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in s).strip("_")

def read_layer_smart(path: str, layer: str) -> gpd.GeoDataFrame:
    """
    Intenta leer 'layer'; si falla, lista capas y sugiere una que empiece por 'manzanas'.
    """
    try:
        return gpd.read_file(path, layer=layer)
    except Exception:
        if _list_layers is None:
            raise RuntimeError(f"No se pudo abrir layer='{layer}' y no está disponible pyogrio.list_layers para sugerencias.")
        layers = [t[0] if isinstance(t, (list, tuple)) else t for t in _list_layers(path)]
        candidates = [l for l in layers if str(l).lower().startswith("manzanas")]
        suggestion = candidates[0] if candidates else (layers[0] if layers else None)
        msg = f"La capa '{layer}' no existe en {os.path.basename(path)}.\nCapas disponibles: {layers}."
        if suggestion:
            msg += f"\nSugerencia: usa --layer {suggestion}"
        raise RuntimeError(msg)

# ─────────────────────────────────────────────────────────────
# Núcleo: OLS (statsmodels) + Moran (esda)
# ─────────────────────────────────────────────────────────────
def ols_moran_one(gdf_in: gpd.GeoDataFrame, yname: str, xnames: List[str],
                  weights_type: str, k: int, robust: Optional[str],
                  alcaldia_name: str) -> Tuple[Dict, pd.DataFrame, gpd.GeoDataFrame]:
    """
    Ejecuta OLS + Moran en el subconjunto dado (gdf_in).
    Devuelve: dict resumen, DF coeficientes, GDF con yhat/residuos.
    """
    gdf = gdf_in.copy()
    cols_need = [yname] + xnames
    missing = [c for c in cols_need if c not in gdf.columns]
    if missing:
        raise ValueError(f"Faltan columnas en el GDF: {missing}")

    # Numérico + dropna
    safe_numeric(gdf, cols_need)
    gdf = gdf.dropna(subset=cols_need)
    n = len(gdf)
    if n < len(xnames) + 5:
        raise ValueError(f"Pocas filas ({n}) para OLS en {alcaldia_name}")

    # Matrices
    y = gdf[yname].values.astype(float)
    Xmat = gdf[xnames].values.astype(float)

    # Añadir constante (1s)
    X = sm.add_constant(Xmat, has_constant="add")

    # Robustez: mapear a cov_type de statsmodels
    covmap = {"white": "HC0", "hc0": "HC0", "hc1": "HC1", "hc2": "HC2", "hc3": "HC3"}
    cov_type = covmap.get((robust or "").lower(), None)

    # OLS
    res = sm.OLS(y, X).fit(cov_type=cov_type) if cov_type else sm.OLS(y, X).fit()

    # Extraer resultados (asegurando ndarrays)
    betas = np.asarray(res.params, dtype=float)
    se    = np.asarray(res.bse, dtype=float)
    r2    = float(res.rsquared)
    ar2   = float(res.rsquared_adj)
    aic   = float(res.aic)

    # Predicciones y residuos (asegurando ndarrays)
    yhat  = np.asarray(res.fittedvalues, dtype=float)
    resid = np.asarray(res.resid, dtype=float)

    # Pesos & Moran
    gdf_w = ensure_projected(gdf)
    W = build_weights(gdf_w, method=weights_type, k=k)
    mor = Moran(resid, W)

    # Resumen
    summary = {
        "alcaldia": alcaldia_name,
        "n": int(n),
        "k_params": int(X.shape[1]),
        "r2": r2,
        "adj_r2": ar2,
        "AIC": aic,
        "weights": weights_type,
        "knn_k": (k if weights_type == "knn" else (k if isinstance(W, KNN) else None)),
        "moran_I": float(mor.I),
        "moran_z_norm": float(mor.z_norm),
        "moran_p_norm": float(mor.p_norm),
        "islands": int(len(getattr(W, "islands", [])))
    }

    # Coefs tidy
    coef_rows = []
    for i, nm in enumerate(["const"] + xnames):
        coef_rows.append({
            "alcaldia": alcaldia_name,
            "variable": nm,
            "beta": float(betas[i]),
            "std_err": float(se[i])
        })
    coef_df = pd.DataFrame(coef_rows)

    # Geo salida
    gdf_out = gdf.copy()
    gdf_out["OLS_yhat"]  = yhat
    gdf_out["OLS_resid"] = resid

    return summary, coef_df, gdf_out

# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    args = parse_args()
    args.xvars = [s.strip() for s in args.xvars.split(",") if s.strip()]

    os.makedirs(args.outdir, exist_ok=True)

    log("=== OLS + Moran's I (CDMX · statsmodels) ===")
    log(f"GPKG:   {args.gpkg} | layer: {args.layer}")
    log(f"Y:      {args.yvar}")
    log(f"X:      {args.xvars}")
    log(f"W:      {args.weights} (k={args.k}) | robust={args.robust}")
    log(f"Salida: {args.outdir} | save_gpkg={args.save_gpkg}")

    # Cargar capa (con autocorrección de layer)
    gdf_all = read_layer_smart(args.gpkg, args.layer)

    # Detectar columna de alcaldía
    mun_col = find_mun_col(gdf_all)
    if mun_col is None:
        raise RuntimeError("No se encontró columna de alcaldía (NOM_MUN/alcaldia/municipio/MUN)")

    # Contenedores
    summaries: List[Dict] = []
    coef_list: List[pd.DataFrame] = []

    # ── Loop por alcaldía
    for alc, gsub in gdf_all.groupby(mun_col):
        log(f"\n→ Alcaldía: {alc}  (n={len(gsub)})")
        try:
            summ, coef_df, gdf_out = ols_moran_one(
                gsub, args.yvar, args.xvars,
                weights_type=args.weights, k=args.k, robust=args.robust,
                alcaldia_name=str(alc)
            )
            summaries.append(summ)
            coef_list.append(coef_df)

            if args.save_gpkg:
                out_gpkg = os.path.join(args.outdir, f"OLS_residuos_{slug(alc)}.gpkg")
                gdf_out.to_file(out_gpkg, layer="manzanas", driver="GPKG")
                log(f"   📦 GPKG alcaldía -> {out_gpkg}")
        except Exception as e:
            log(f"   ❌ Saltando {alc}: {e}")

    # ── Ciudad completa
    log("\n→ Ciudad completa")
    try:
        summ_city, coef_city, gdf_city = ols_moran_one(
            gdf_all, args.yvar, args.xvars,
            weights_type=args.weights, k=args.k, robust=args.robust,
            alcaldia_name="CIUDAD"
        )
        summaries.append(summ_city)
        coef_list.append(coef_city)

        if args.save_gpkg:
            out_gpkg = os.path.join(args.outdir, "OLS_residuos_CIUDAD.gpkg")
            gdf_city.to_file(out_gpkg, layer="manzanas", driver="GPKG")
            log(f"   📦 GPKG ciudad -> {out_gpkg}")
    except Exception as e:
        log(f"   ❌ OLS ciudad: {e}")

    # ── Exportar CSVs
    if summaries:
        df_sum = pd.DataFrame(summaries)
        sum_csv = os.path.join(args.outdir, "OLS_Moran_summary_by_alcaldia.csv")
        df_sum.sort_values(["alcaldia"]).to_csv(sum_csv, index=False)
        log(f"\n📄 Resumen OLS+Moran -> {sum_csv}")

    if coef_list:
        df_coef = pd.concat(coef_list, ignore_index=True)
        coef_csv = os.path.join(args.outdir, "OLS_coefficients_by_alcaldia.csv")
        df_coef.to_csv(coef_csv, index=False)
        log(f"📄 Coeficientes OLS -> {coef_csv}")

    log("\n=== FIN ===")
