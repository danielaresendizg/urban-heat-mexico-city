# compare_OLS_GWR_moran.py
# -*- coding: utf-8 -*-
"""
Comparativo OLS vs GWR (flex) — Soporta:
  A) Carpeta con GPKG por alcaldía  (--gpkg-dir + --pattern)
  B) GPKG único consolidado (merge)  (--merged-gpkg + --merged-layer)

Calcula para GWR (por alcaldía):
  - R²_GWR global (reconstruyendo ŷ desde coef_* y X)
  - Moran's I de residuos (Queen; fallback KNN)

Si pasas el CSV OLS, hace comparativo OLS vs GWR.

Salidas:
  - GWR_Moran_summary_by_alcaldia.csv
  - Compare_OLS_vs_GWR_moran.csv (si das --ols-summary)
  - (opcional) GPKG(s) con GWR_yhat y GWR_resid
"""

import os, glob, argparse
from typing import List, Optional, Dict
import numpy as np
import pandas as pd
import geopandas as gpd
from esda import Moran
from libpysal.weights import Queen, KNN

try:
    from pyogrio import list_layers as _list_layers
except Exception:
    _list_layers = None

# ───────── Utils ─────────
def log(m): print(m, flush=True)
def slug(s: str) -> str: return "".join(ch if ch.isalnum() else "_" for ch in str(s)).strip("_")
def to_num(df: pd.DataFrame, cols: List[str]):
    for c in cols:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")

def ensure_projected(gdf: gpd.GeoDataFrame, epsg="EPSG:32614") -> gpd.GeoDataFrame:
    try:
        if gdf.crs is None or gdf.crs.to_string().lower() != epsg.lower(): return gdf.to_crs(epsg)
        return gdf
    except Exception:
        return gdf.to_crs(epsg)

def build_weights(gdf: gpd.GeoDataFrame, method="queen", k=8):
    method = (method or "queen").lower()
    if method == "queen":
        try:
            w = Queen.from_dataframe(gdf, ids=gdf.index)
            if hasattr(w, "islands") and len(w.islands) > 0:
                log(f"  ⚠️ Queen encontró {len(w.islands)} islas → fallback KNN(k={k})")
                w = KNN.from_dataframe(gdf, k=k, ids=gdf.index)
        except Exception:
            log("  ⚠️ Queen falló → KNN")
            w = KNN.from_dataframe(gdf, k=k, ids=gdf.index)
    else:
        w = KNN.from_dataframe(gdf, k=k, ids=gdf.index)
    w.transform = "R"
    return w

def read_layer_smart(path: str, layer: str) -> gpd.GeoDataFrame:
    try:
        return gpd.read_file(path, layer=layer)
    except Exception:
        if _list_layers is None: raise
        layers = [t[0] if isinstance(t,(list,tuple)) else t for t in _list_layers(path)]
        cand = next((l for l in layers if str(l).lower().startswith("manzanas")), (layers[0] if layers else None))
        raise RuntimeError(f"No existe layer='{layer}' en {os.path.basename(path)}. Capas={layers}. Sugerencia: {cand or '(elige una de la lista)'}")

def find_mun_col(df: pd.DataFrame) -> Optional[str]:
    for c in ["NOM_MUN","alcaldia","municipio","MUN"]:
        if c in df.columns: return c
    return None

def r2_from_residuals(y: np.ndarray, resid: np.ndarray) -> float:
    y = np.asarray(y, float); resid = np.asarray(resid, float)
    sst = np.sum((y - y.mean())**2); ssr = np.sum(resid**2)
    return float(1 - ssr/max(sst, 1e-12))

# ───────── Core ─────────
def compute_gwr_resid_moran(gdf: gpd.GeoDataFrame, yname: str,
                            weights: str, k: int) -> Dict:
    cols = gdf.columns.tolist()
    y = pd.to_numeric(gdf[yname], errors="coerce")
    if y.isna().all(): raise ValueError(f"'{yname}' vacío/no numérico")

    # Encuentra pares coef_* y columnas X (excluye intercepto)
    coef_cols = [c for c in cols if c.startswith("coef_")]
    base_vars = []
    for c in coef_cols:
        if c == "coef_Intercept": continue
        v = c.replace("coef_", "")
        if v in cols: base_vars.append(v)
    base_vars = sorted(set(base_vars))
    if not base_vars: raise ValueError("No hallé pares coef_* y columnas X")

    # ŷ_GWR = b0 + Σ b_i * X_i
    yhat = pd.to_numeric(gdf.get("coef_Intercept"), errors="coerce")
    if yhat is None or yhat.isna().all(): yhat = pd.Series(0.0, index=gdf.index, dtype="float64")
    for v in base_vars:
        beta = pd.to_numeric(gdf[f"coef_{v}"], errors="coerce")
        x    = pd.to_numeric(gdf[v], errors="coerce")
        yhat = yhat.add(beta * x, fill_value=0.0)

    resid = (y - yhat).astype(float)

    gproj = ensure_projected(gdf)
    W = build_weights(gproj, method=weights, k=k)
    mor = Moran(np.asarray(resid, float), W)
    r2g = r2_from_residuals(np.asarray(y, float), np.asarray(resid, float))

    return {
        "n": int(len(gdf)),
        "r2_gwr": r2g,
        "moran_I_gwr": float(mor.I),
        "moran_p_gwr": float(mor.p_norm),
        "moran_z_gwr": float(mor.z_norm),
        "yhat": np.asarray(yhat, float),
        "resid": np.asarray(resid, float),
    }

# ───────── CLI ─────────
def parse_args():
    ap = argparse.ArgumentParser(description="Comparar OLS vs GWR (R² y Moran de residuos) por alcaldía")
    # Modo A (carpeta de GPKG por alcaldía)
    ap.add_argument("--gpkg-dir", help="Directorio con GPKG por alcaldía (modo A)")
    ap.add_argument("--pattern", default="MGWR_coeficientes_*.gpkg", help="Patrón de archivos (modo A)")
    ap.add_argument("--layer", default="manzanas", help="Layer dentro de cada GPKG (modo A)")
    # Modo B (GPKG único merge)
    ap.add_argument("--merged-gpkg", help="Ruta a GPKG único consolidado (modo B)")
    ap.add_argument("--merged-layer", help="Layer dentro del GPKG único (modo B)")
    # Comunes
    ap.add_argument("--yvar", default="Ta_mean", help="Variable dependiente")
    ap.add_argument("--weights", default="queen", choices=["queen","knn"], help="Pesos para Moran")
    ap.add_argument("--k", type=int, default=8, help="k para KNN")
    ap.add_argument("--ols-summary", default=None, help="CSV: OLS_Moran_summary_by_alcaldia.csv")
    ap.add_argument("--save-gpkg", action="store_true", help="Guardar GPKG con GWR_yhat y GWR_resid")
    ap.add_argument("--outdir", default=None, help="Directorio de salida (default=carpeta de entrada)")
    return ap.parse_args()

if __name__ == "__main__":
    args = parse_args()

    # Detectar modo
    mode_a = bool(args.gpkg_dir)
    mode_b = bool(args.merged_gpkg and args.merged_layer)
    if not (mode_a or mode_b):
        raise SystemExit("Debes indicar --gpkg-dir (modo A) **o** --merged-gpkg y --merged-layer (modo B)")

    outdir = args.outdir or (args.gpkg_dir if mode_a else os.path.dirname(args.merged_gpkg))
    os.makedirs(outdir, exist_ok=True)

    summaries = []

    if mode_a:
        log(">> Modo A (carpeta con GPKG por alcaldía)")
        paths = sorted(glob.glob(os.path.join(args.gpkg_dir, args.pattern)))
        if not paths:
            raise SystemExit(f"No encontré GPKG con patrón {args.pattern} en {args.gpkg_dir}")

        for p in paths:
            try:
                gdf = read_layer_smart(p, args.layer)
                mun_col = find_mun_col(gdf)
                if mun_col:
                    m = gdf[mun_col].astype(str).mode(dropna=True)
                    alc = str(m.iloc[0]) if not m.empty else os.path.basename(p)
                else:
                    alc = os.path.basename(p)

                log(f"\n→ {os.path.basename(p)} | alcaldía: {alc} | n={len(gdf)}")
                res = compute_gwr_resid_moran(gdf, args.yvar, args.weights, args.k)

                if args.save_gpkg:
                    out_g = gdf.copy()
                    out_g["GWR_yhat"]  = res["yhat"]
                    out_g["GWR_resid"] = res["resid"]
                    out_path = os.path.join(outdir, f"GWR_residuos_{slug(alc)}.gpkg")
                    out_g.to_file(out_path, layer=args.layer, driver="GPKG")
                    log(f"   📦 GPKG con residuales → {out_path}")

                summaries.append({
                    "alcaldia": alc, "n": res["n"], "R2_GWR": res["r2_gwr"],
                    "MoranI_GWR": res["moran_I_gwr"], "p_Moran_GWR": res["moran_p_gwr"],
                    "z_Moran_GWR": res["moran_z_gwr"],
                })
            except Exception as e:
                log(f"   ❌ Saltando {os.path.basename(p)}: {e}")

    else:
        log(">> Modo B (GPKG único merge)")
        gdf_all = read_layer_smart(args.merged_gpkg, args.merged_layer)
        mun_col = find_mun_col(gdf_all)
        if not mun_col:
            raise SystemExit("El GPKG 'merge' no tiene col de alcaldía (NOM_MUN/alcaldia/municipio/MUN).")

        for alc, gsub in gdf_all.groupby(mun_col):
            gsub = gsub.copy()
            log(f"\n→ Alcaldía: {alc} | n={len(gsub)}")
            try:
                res = compute_gwr_resid_moran(gsub, args.yvar, args.weights, args.k)
                if args.save_gpkg:
                    out_g = gsub.copy()
                    out_g["GWR_yhat"]  = res["yhat"]
                    out_g["GWR_resid"] = res["resid"]
                    out_path = os.path.join(outdir, f"GWR_residuos_{slug(alc)}.gpkg")
                    out_g.to_file(out_path, layer="manzanas", driver="GPKG")
                    log(f"   📦 GPKG con residuales → {out_path}")

                summaries.append({
                    "alcaldia": str(alc), "n": res["n"], "R2_GWR": res["r2_gwr"],
                    "MoranI_GWR": res["moran_I_gwr"], "p_Moran_GWR": res["moran_p_gwr"],
                    "z_Moran_GWR": res["moran_z_gwr"],
                })
            except Exception as e:
                log(f"   ❌ Saltando {alc}: {e}")

    # Resumen GWR
    df_gwr = pd.DataFrame(summaries).sort_values("alcaldia")
    gwr_csv = os.path.join(outdir, "GWR_Moran_summary_by_alcaldia.csv")
    df_gwr.to_csv(gwr_csv, index=False)
    log(f"\n📄 Resumen GWR → {gwr_csv}")

    # Comparativo con OLS (si se proporciona)
    if args.ols_summary and os.path.exists(args.ols_summary):
        df_ols = pd.read_csv(args.ols_summary)
        if "alcaldia" in df_ols.columns: df_ols["alcaldia"] = df_ols["alcaldia"].astype(str)
        to_num(df_ols, ["r2","adj_r2","moran_p_norm","moran_I","AIC","n"])
        comp = (df_ols.rename(columns={"r2":"R2_OLS","adj_r2":"AdjR2_OLS","moran_p_norm":"p_Moran_OLS","moran_I":"MoranI_OLS"})
                .merge(df_gwr, on="alcaldia", how="inner"))
        comp["delta_R2"] = comp["R2_GWR"] - comp["R2_OLS"]
        comp["improve_R2"] = comp["delta_R2"] > 0
        comp["improve_Moran_p"] = comp["p_Moran_GWR"] > comp["p_Moran_OLS"]  # p mayor = menos autocorr.
        out_comp = os.path.join(outdir, "Compare_OLS_vs_GWR_moran.csv")
        comp.sort_values(["improve_R2","improve_Moran_p","delta_R2"], ascending=[False,False,False]).to_csv(out_comp, index=False)
        log(f"📄 Comparativo OLS vs GWR → {out_comp}")

    log("\n=== FIN ===")
