import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import date

# === CONFIGURACIÓN ===
base_dir = Path("/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana")
gpkg_path = base_dir / "manzanas_IVS_Ta.gpkg"
layer_name = "manzanas_ivs_ta"
figures_dir = Path("figures_heat")
date_suffix = date.today().strftime("%Y%m%d")

# === CARGAR DATOS ===
gdf = gpd.read_file(gpkg_path, layer=layer_name)

# === VARIABLES A ANALIZAR ===
variables = [
    "pct_014", "pct_60plus", "pct_hli", "pct_afro", "pct_disc",
    "pct_inac", "GRAPROES", "PRO_OCUP_C"
]

# === SCATTER PLOTS POR VARIABLE ===
for var in variables:
    plt.figure(figsize=(8, 5))
    sns.scatterplot(x=var, y="Ta_mean", data=gdf, alpha=0.4)
    plt.title(f"Relación entre {var} y Temperatura Promedio")
    plt.xlabel(var)
    plt.ylabel("Temperatura (Ta_clim) °C")
    plt.tight_layout()
    plt.savefig(figures_dir / f"scatter_{var}_Ta_{date_suffix}.pdf")
    plt.savefig(figures_dir / f"scatter_{var}_Ta_{date_suffix}.png")
    plt.savefig(figures_dir / f"scatter_{var}_Ta_{date_suffix}.svg")
    plt.close()

# === MATRIZ DE CORRELACIÓN ===
corr_vars = variables + ["IVS", "Ta_mean"]
corr_matrix = gdf[corr_vars].corr()

plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", fmt=".2f")
plt.title("Matriz de Correlación entre Variables Sociales y Temperatura")
plt.tight_layout()
plt.savefig(figures_dir / f"heatmap_corr_variables_{date_suffix}.pdf")
plt.savefig(figures_dir / f"heatmap_corr_variables_{date_suffix}.png")
plt.savefig(figures_dir / f"heatmap_corr_variables_{date_suffix}.svg")
plt.close()

print("✅ Gráficos y matriz de correlación generados correctamente en 'figures_heat'.")

