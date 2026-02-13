import geopandas as gpd
import pandas as pd
import numpy as np
from mgwr.gwr import GWR, Sel_BW
from sklearn.preprocessing import StandardScaler
import os

# --- Cargar datos ---
gdf = gpd.read_file("manzanas_IVS_20250724.gpkg")
gdf = gdf.dropna(subset=["pct_0a5", "Ta_mean"])
gdf = gdf[gdf.is_valid]

# --- Preparar coordenadas y variables ---
coords = np.array(list(zip(gdf.geometry.centroid.x, gdf.geometry.centroid.y)))
y = gdf[["Ta_mean"]].values
X = gdf[["pct_0a5"]].values
X = StandardScaler().fit_transform(X)

# --- Bandwidth óptimo ---
bw = Sel_BW(coords, y, X).search()
print(f"Bandwidth óptimo: {bw}")

# --- Ajustar MGWR ---
model = GWR(coords, y, X, bw)
results = model.fit()

# --- Guardar coeficientes en GeoDataFrame ---
gdf["gwr_coef_pct_0a5"] = results.params.flatten()
gdf.to_file("gwr_results_pct_0a5.gpkg", driver="GPKG")

# --- Crear tabla resumen global ---
summary_data = {
    "Variable": ["pct_0a5"],
    "Bandwidth": [bw],
    "N_observaciones": [len(gdf)],
    "Coef_mean": [np.mean(results.params)],
    "Coef_min": [np.min(results.params)],
    "Coef_max": [np.max(results.params)],
    "Coef_std": [np.std(results.params)],
    "R2_adj": [results.adj_R2],
    "AICc": [results.aicc]
}

summary_df = pd.DataFrame(summary_data)
summary_df.to_csv("mgwr_summary_pct_0a5.csv", index=False)
print("Resumen guardado en mgwr_summary_pct_0a5.csv")
