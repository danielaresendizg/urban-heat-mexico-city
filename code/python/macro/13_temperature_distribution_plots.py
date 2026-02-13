import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from pathlib import Path
from datetime import date

# === CONFIGURACIÓN ===
base_dir = Path("/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana")
gpkg_path = base_dir / "manzanas_IVS_Ta.gpkg"
layer_name = "manzanas_ivs_ta"
figures_dir = Path("figures_heat")
date_suffix = date.today().strftime("%Y%m%d")
figures_dir.mkdir(exist_ok=True)

# === CARGAR DATOS ===
gdf = gpd.read_file(gpkg_path, layer=layer_name)

# === FIGURA 1: Histograma IVS ===
plt.figure(figsize=(8, 5))
sns.histplot(gdf["IVS"].dropna(), bins=30, kde=True, color="skyblue")
plt.title("Distribución del Índice de Vulnerabilidad Social (IVS)")
plt.xlabel("IVS")
plt.ylabel("Número de Manzanas")
plt.tight_layout()
plt.savefig(figures_dir / f"hist_IVS_{date_suffix}.pdf")
plt.savefig(figures_dir / f"hist_IVS_{date_suffix}.png")
plt.savefig(figures_dir / f"hist_IVS_{date_suffix}.svg")
plt.close()

# === FIGURA 2: Histograma Temperatura ===
plt.figure(figsize=(8, 5))
sns.histplot(gdf["Ta_mean"].dropna(), bins=30, kde=True, color="salmon")
plt.title("Distribución de Temperatura Promedio (Ta_clim)")
plt.xlabel("Temperatura (Ta_clim) °C")
plt.ylabel("Número de Manzanas")
plt.tight_layout()
plt.savefig(figures_dir / f"hist_Ta_{date_suffix}.pdf")
plt.savefig(figures_dir / f"hist_Ta_{date_suffix}.png")
plt.savefig(figures_dir / f"hist_Ta_{date_suffix}.svg")
plt.close()

# === FIGURA 3: Scatter plot IVS vs Temperatura ===
plt.figure(figsize=(8, 5))
sns.scatterplot(x="IVS", y="Ta_mean", data=gdf, alpha=0.4)
plt.title("Relación entre IVS y Temperatura Promedio")
plt.xlabel("IVS")
plt.ylabel("Temperatura (Ta_clim) °C")
plt.tight_layout()
plt.savefig(figures_dir / f"scatter_IVS_Ta_{date_suffix}.pdf")
plt.savefig(figures_dir / f"scatter_IVS_Ta_{date_suffix}.png")
plt.savefig(figures_dir / f"scatter_IVS_Ta_{date_suffix}.svg")
plt.close()

# === FIGURA 4: Boxplot de Temperatura por terciles de IVS ===
plt.figure(figsize=(8, 5))
sns.boxplot(x="IVS_cat3", y="Ta_mean", data=gdf, palette="pastel")
plt.title("Temperatura Promedio por Categoría de IVS")
plt.xlabel("Categoría IVS (Baja, Media, Alta)")
plt.ylabel("Temperatura (Ta_clim) °C")
plt.tight_layout()
plt.savefig(figures_dir / f"boxplot_Ta_IVS_cat3_{date_suffix}.pdf")
plt.savefig(figures_dir / f"boxplot_Ta_IVS_cat3_{date_suffix}.png")
plt.savefig(figures_dir / f"boxplot_Ta_IVS_cat3_{date_suffix}.svg")
plt.close()

# === FIGURA 5: Mapa Bivariado (IVS + Temperatura) ===
# Crear cuartiles
gdf["IVS_quartile"] = pd.qcut(gdf["IVS"], 4, labels=["Q1", "Q2", "Q3", "Q4"])
gdf["Ta_quartile"] = pd.qcut(gdf["Ta_mean"], 4, labels=["Q1", "Q2", "Q3", "Q4"])

plt.figure(figsize=(10, 10))
gdf.plot(column="IVS_quartile", cmap="Blues", legend=True)
plt.title("Mapa de Cuartiles del IVS")
plt.axis("off")
plt.savefig(figures_dir / f"map_IVS_quartile_{date_suffix}.pdf")
plt.savefig(figures_dir / f"map_IVS_quartile_{date_suffix}.png")
plt.savefig(figures_dir / f"map_IVS_quartile_{date_suffix}.svg")
plt.close()

plt.figure(figsize=(10, 10))
gdf.plot(column="Ta_quartile", cmap="Reds", legend=True)
plt.title("Mapa de Cuartiles de Temperatura")
plt.axis("off")
plt.savefig(figures_dir / f"map_Ta_quartile_{date_suffix}.pdf")
plt.savefig(figures_dir / f"map_Ta_quartile_{date_suffix}.png")
plt.savefig(figures_dir / f"map_Ta_quartile_{date_suffix}.svg")
plt.close()

print("✅ Todas las figuras han sido generadas y guardadas en la carpeta 'figures'.")

