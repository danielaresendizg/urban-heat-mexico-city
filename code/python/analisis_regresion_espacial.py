# analisis_regresion_espacial.py
# Análisis OLS, Spatial Lag, GWR y mapas R2 para Ta_max en CDMX (nivel manzana)

import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import contextily as cx
from spreg import OLS, ML_Lag
from mgwr.gwr import GWR
from mgwr.sel_bw import Sel_BW
from libpysal.weights import KNN
from esda.moran import Moran

# ---------------------------------------------------------------
# 1. Cargar datos
GPKG_PATH = "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/manzana_thermal-IVS.gpkg"
gdf = gpd.read_file(GPKG_PATH)

# Ajusta si cambia el nombre de la columna de alcaldía
alc_col = "ALCALDIA" if "ALCALDIA" in gdf.columns else "ALC"

predictors = [
    'IVS',
    'pct_014', 'pct_60plus', 'GRAPROES', 'pct_disc', 'pct_hli', 'pct_inac'
]
response = 'Ta_max'

# Elimina NaN/infs
df = gdf[[response] + predictors + ['geometry']].replace([np.inf, -np.inf], np.nan).dropna().copy()
df['x'] = df.geometry.centroid.x
df['y'] = df.geometry.centroid.y

# ---------------------------------------------------------------
# 2. OLS clásico
print("=== OLS CLÁSICO ===")
X = df[predictors].values
y = df[response].values.reshape(-1,1)
ols = OLS(y, X, name_y=response, name_x=predictors)
print(ols.summary)

# ---------------------------------------------------------------
# 3. Spatial Lag Model
print("=== SPATIAL LAG ===")
coords = list(zip(df['x'], df['y']))
w = KNN.from_array(coords, k=8)
w.transform = 'r'
lag = ML_Lag(y, X, w=w, name_y=response, name_x=predictors)
print(lag.summary)

# ---------------------------------------------------------------
# 4. Moran de residuos OLS
print("=== MORAN'S I EN RESIDUOS OLS ===")
residuals = ols.u.flatten()
moran = Moran(residuals, w)
print(f"Moran's I: {moran.I:.4f}, p-value: {moran.p_sim:.4f}")

# ---------------------------------------------------------------
# 5. GWR
print("=== GWR ===")
g_coords = df[['x','y']].values
bw = Sel_BW(g_coords, y, X).search()
print(f"Bandwidth óptimo: {bw}")
gwr = GWR(g_coords, y, X, bw=bw)
gwr_results = gwr.fit()
print(gwr_results.summary())

# ---------------------------------------------------------------
# 6. Mapa de R2 local (GWR)
df['localR2'] = gwr_results.localR2
ax = df.plot(column='localR2', cmap='plasma', legend=True,
             figsize=(10,8), alpha=0.8, edgecolor='none')
plt.title("R² local (GWR) para Ta_max")
cx.add_basemap(ax, crs=df.crs.to_string(), source=cx.providers.CartoDB.Positron, alpha=0.4)
plt.tight_layout()
plt.savefig("figures_median_scale/mapa_localR2_gwr.png", dpi=300)
plt.close()
print("✓ Mapa R² local guardado: figures_median_scale/mapa_localR2_gwr.png")

# ---------------------------------------------------------------
# 7. Mapa de residuos GWR
df['residuals'] = gwr_results.resid_response.flatten()
ax = df.plot(column='residuals', cmap='RdBu', legend=True,
             figsize=(10,8), alpha=0.8, edgecolor='none')
plt.title("Residuos GWR (Ta_max)")
cx.add_basemap(ax, crs=df.crs.to_string(), source=cx.providers.CartoDB.Positron, alpha=0.4)
plt.tight_layout()
plt.savefig("figures_median_scale/mapa_residuos_gwr.png", dpi=300)
plt.close()
print("✓ Mapa residuos GWR guardado: figures_median_scale/mapa_residuos_gwr.png")

print("\n🚀 ¡Listo! Checa tu terminal para resultados numéricos y la carpeta figures_median_scale para mapas.")
