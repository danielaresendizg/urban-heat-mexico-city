# -*- coding: utf-8 -*-
"""
Hotspots térmico-sociales con GWR — Umbrales fijos 26/28 °C
- Peligro:        26.0 ≤ Ta_mean < 28.0  & (coef>0, t>1.96)
- Peligro extremo:      Ta_mean ≥ 28.0   & (coef>0, t>2.58)

Crea columnas:
  - is_hot_26 (26≤Ta<28), is_hot_28 (Ta≥28)
  - hot26_<var>, hot28_<var>
  - hot26_any_social, hot28_any_social
  - hot26_count_social, hot28_count_social
  - peligro_cat (0/1/2) general para mapa combinado

Salidas:
  - NUEVO layer en el mismo GPKG (no sobrescribe el original)
  - CSV espejo (sin geometría)
  - PNG combinado general (400 dpi)
  - PNG combinado por predictor (400 dpi, 0/1/2)
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
import numpy as np

# ───────────────────────── Rutas ─────────────────────────
MANZANAS_GPKG = Path(
    "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/"
    "Dissertation/01_data/GWR/GWR_merge/manzanas_master_con_GWR_spacematrix_v3lite.gpkg"
)
LAYER_IN   = "manzanas"                 # capa original
LAYER_OUT  = "manzanas_con_hotspots"    # NUEVA capa de salida
CSV_OUT    = MANZANAS_GPKG.parent / "manzanas_con_hotspots.csv"

# Figuras
FIG_DIR    = MANZANAS_GPKG.parent / "figs_hotspots"
PNG_GENERAL= FIG_DIR / "hotspots_GWR_umbral_26_28_combined.png"

# ─────────────── Umbrales térmicos y t-críticos ───────────
DANGER_MIN = 26.0    # peligro: 26 ≤ Ta < 28
EXTREME_MIN= 28.0    # extremo: Ta ≥ 28
T_26 = 1.96          # t crítico para peligro
T_28 = 2.58          # t crítico para peligro extremo

# ─────────────────────── Cargar datos ─────────────────────
gdf = gpd.read_file(MANZANAS_GPKG, layer=LAYER_IN)
cols = gdf.columns.tolist()

if "Ta_mean" not in cols:
    raise ValueError("No encontré la columna 'Ta_mean' en el layer.")
gdf["Ta_mean"] = pd.to_numeric(gdf["Ta_mean"], errors="coerce")

# Detectar predictores sociales (coef_* & tval_*), excluyendo Intercept
coef_cols = [c for c in cols if c.startswith("coef_") and c != "coef_Intercept"]
tval_cols = [c for c in cols if c.startswith("tval_") and c != "tval_Intercept"]
base_coef = [c.replace("coef_", "") for c in coef_cols]
base_tval = [c.replace("tval_", "") for c in tval_cols]
predictors = sorted(set(base_coef).intersection(base_tval))
if not predictors:
    raise ValueError("No hay predictores sociales con pares (coef_*, tval_*).")

print("Predictores sociales detectados:", predictors)
print(f"Umbrales → peligro: 26.0–27.9999 °C (t>{T_26}), extremo: ≥{EXTREME_MIN:.1f} °C (t>{T_28})")

# ──────────────── Flags térmicos de transparencia ─────────
gdf["is_hot_26"] = ((gdf["Ta_mean"] >= DANGER_MIN) & (gdf["Ta_mean"] < EXTREME_MIN)).astype("int8")
gdf["is_hot_28"] = (gdf["Ta_mean"] >= EXTREME_MIN).astype("int8")

# ─────────────── Crear columnas hotspot por predictor ─────
hot26_cols, hot28_cols = [], []
for var in predictors:
    c_col = f"coef_{var}"
    t_col = f"tval_{var}"
    gdf[c_col] = pd.to_numeric(gdf[c_col], errors="coerce")
    gdf[t_col] = pd.to_numeric(gdf[t_col], errors="coerce")

    col26 = f"hot26_{var}"  # 26 ≤ Ta < 28 + GWR (t>1.96, coef>0)
    col28 = f"hot28_{var}"  # Ta ≥ 28        + GWR (t>2.58, coef>0)

    gdf[col26] = (
        (gdf[c_col] > 0) &
        (gdf[t_col] > T_26) &
        (gdf["Ta_mean"] >= DANGER_MIN) &
        (gdf["Ta_mean"] <  EXTREME_MIN)
    ).astype("int8")

    gdf[col28] = (
        (gdf[c_col] > 0) &
        (gdf[t_col] > T_28) &
        (gdf["Ta_mean"] >= EXTREME_MIN)
    ).astype("int8")

    hot26_cols.append(col26)
    hot28_cols.append(col28)

# ─────────────────────── Agregados útiles ─────────────────
gdf["hot26_any_social"]   = (gdf[hot26_cols].sum(axis=1) > 0).astype("int8")
gdf["hot28_any_social"]   = (gdf[hot28_cols].sum(axis=1) > 0).astype("int8")
gdf["hot26_count_social"] = gdf[hot26_cols].sum(axis=1).astype("int16")
gdf["hot28_count_social"] = gdf[hot28_cols].sum(axis=1).astype("int16")

# Categoría general para mapa unificado: 0=no, 1=peligro (26–<28), 2=extremo (≥28)
gdf["peligro_cat"] = np.select(
    [
        gdf["hot28_any_social"].eq(1),
        gdf["hot26_any_social"].eq(1)
    ],
    [2, 1],
    default=0
).astype("int8")

# ───────────────────────── Guardar GPKG/CSV ──────────────
print(f"→ Escribiendo NUEVO layer: {LAYER_OUT}")
gdf.to_file(MANZANAS_GPKG, layer=LAYER_OUT, driver="GPKG")

print(f"→ Escribiendo CSV: {CSV_OUT.name}")
gdf.drop(columns="geometry").to_csv(CSV_OUT, index=False, encoding="utf-8")

print("Listo ✅  (layer original intacto; nuevo layer + CSV con umbrales 26/28)")

# ==========================
#      FIGURAS (400 dpi)
# ==========================
import matplotlib
matplotlib.use("Agg")  # backend sin GUI
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

FIG_DIR.mkdir(exist_ok=True)

# Paleta combinada: 0=gris, 1=naranja, 2=rojo oscuro
COLOR_MAP = {0: "#f2f2f2", 1: "#ef6548", 2: "#b30000"}

def _plot_combined(gdf_, cat_series, titulo, out_png):
    tmp = gdf_.copy()
    tmp["_color_tmp"] = pd.Series(cat_series).map(COLOR_MAP)
    fig, ax = plt.subplots(figsize=(9, 9))
    try:
        gdf_.boundary.plot(ax=ax, linewidth=0.08, color="#ffffff")
    except Exception:
        pass
    tmp.plot(ax=ax, color=tmp["_color_tmp"], linewidth=0)

    ax.set_axis_off()
    ax.set_title(titulo, fontsize=12)

    legend_patches = [
        mpatches.Patch(color=COLOR_MAP[0], label="Sin hotspot social"),
        mpatches.Patch(color=COLOR_MAP[1], label="Peligro (26–<28 °C + GWR+)"),
        mpatches.Patch(color=COLOR_MAP[2], label="Peligro extremo (≥ 28 °C + GWR+)"),
    ]
    ax.legend(handles=legend_patches, loc="lower left", frameon=True, fontsize=9)

    plt.savefig(out_png, dpi=400, bbox_inches="tight", facecolor="white")
    plt.close()

# — PNG combinado general —
title_general = ("Hotspots térmico-sociales (GWR) — Umbrales fijos\n"
                 "gris: sin hotspot · naranja: 26–<28 °C · rojo: ≥28 °C")
_plot_combined(gdf, gdf["peligro_cat"], title_general, PNG_GENERAL)

# — PNG combinado por predictor —
#   Para cada predictor generamos una categoría 0/1/2:
#   2 si hot28_var==1, 1 si hot26_var==1, 0 en otro caso (disyuntos por rango térmico)
for var in predictors:
    cat_var = np.select(
        [
            gdf[f"hot28_{var}"].eq(1),
            gdf[f"hot26_{var}"].eq(1)
        ],
        [2, 1],
        default=0
    ).astype("int8")
    out_png = FIG_DIR / f"hotspots_GWR_umbral_26_28_{var}.png"
    title    = f"{var} — Hotspot social por umbral (26–<28 / ≥28 °C)"
    _plot_combined(gdf, cat_var, title, out_png)

print(f"→ PNG general: {PNG_GENERAL}")
print(f"→ PNG por predictor: {len(predictors)} archivos en {FIG_DIR}")
