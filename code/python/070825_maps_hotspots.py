import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ======= Cargar datos =======
MANZANAS_GPKG = Path("/Users/danielaresendiz/.../manzanas_master_con_GWR_spacematrix_v3lite.gpkg")
LAYER_IN = "manzanas"

gdf = gpd.read_file(MANZANAS_GPKG, layer=LAYER_IN)

# Detectar predictores sociales automáticamente
coef_cols = [c for c in gdf.columns if c.startswith("coef_") and c != "coef_Intercept"]
tval_cols = [c for c in gdf.columns if c.startswith("tval_") and c != "tval_Intercept"]
base_coef = [c.replace("coef_", "") for c in coef_cols]
base_tval = [c.replace("tval_", "") for c in tval_cols]
predictors = sorted(set(base_coef).intersection(base_tval))

# ======= Carpeta de salida =======
FIG_DIR_EN = MANZANAS_GPKG.parent / "figs_hotspots_EN"
FIG_DIR_EN.mkdir(exist_ok=True)

# ======= Paleta de colores =======
COLOR_MAP_EN = {0: "#f2f2f2", 1: "#ffb366", 2: "#e60000"}

def _plot_combined_EN(gdf_, cat_series, title, out_png):
    tmp = gdf_.copy()
    tmp["_color_tmp"] = pd.Series(cat_series).map(COLOR_MAP_EN)
    fig, ax = plt.subplots(figsize=(9, 9))
    try:
        gdf_.boundary.plot(ax=ax, linewidth=0.08, color="#ffffff")
    except Exception:
        pass
    tmp.plot(ax=ax, color=tmp["_color_tmp"], linewidth=0)

    ax.set_axis_off()
    ax.set_title(title, fontsize=12)

    legend_patches = [
        mpatches.Patch(color=COLOR_MAP_EN[0], label="No social hotspot"),
        mpatches.Patch(color=COLOR_MAP_EN[1], label="Warning (26–<28 °C + GWR+)"),
        mpatches.Patch(color=COLOR_MAP_EN[2], label="Extreme danger (≥ 28 °C + GWR+)"),
    ]
    ax.legend(handles=legend_patches, loc="lower left", frameon=True, fontsize=9)

    plt.savefig(out_png, dpi=400, bbox_inches="tight", facecolor="white")
    plt.close()

# ======= PNG general =======
if "peligro_cat" in gdf.columns:
    PNG_GENERAL_EN = FIG_DIR_EN / "hotspots_GWR_threshold_26_28_combined.png"
    title_general_EN = (
        "Thermal–social hotspots (GWR) — Fixed thresholds\n"
        "grey: none · orange: 26–<28 °C · red: ≥28 °C"
    )
    _plot_combined_EN(gdf, gdf["peligro_cat"], title_general_EN, PNG_GENERAL_EN)

# ======= PNGs por predictor =======
for var in predictors:
    if f"hot26_{var}" in gdf.columns or f"hot28_{var}" in gdf.columns:
        cat_var = np.select(
            [
                gdf.get(f"hot28_{var}", pd.Series(0, index=gdf.index)).eq(1),
                gdf.get(f"hot26_{var}", pd.Series(0, index=gdf.index)).eq(1)
            ],
            [2, 1],
            default=0
        ).astype("int8")
        out_png = FIG_DIR_EN / f"hotspots_GWR_threshold_26_28_{var}.png"
        title = f"{var} — Social hotspot by threshold (26–<28 / ≥28 °C)"
        _plot_combined_EN(gdf, cat_var, title, out_png)

print(f"✅ English PNGs saved in: {FIG_DIR_EN}")
