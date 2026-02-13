import geopandas as gpd
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns

# --- Cargar datos ---
gdf = gpd.read_file('/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/manzanas_IVS_20250724.gpkg')

# --- Lista de variables sociales ---
vars_sociales = [
    "pct_0a5", "pct_6a14", "pct_15a64", "pct_65plus",
    "pct_ethnic_afro", "pct_ethnic_ind", "pct_ethnic_other",
    "pct_without_disc", "pct_with_disc",
    "pct_no_school", "pct_elementary_edu", "pct_elementary2_edu", "pct_more_edu",
    "pct_ocup", "pct_desocup", "pct_inac",
    "pct_serv_med", "pct_no_serv_med",
    "pct_pop_auto", "pct_pop_sin_auto",
    "rel_dependencia_0_14", "rel_h_m"
]

# --- Limpiar datos ---
df_clean = gdf[vars_sociales].dropna()

# --- Escalar datos para VIF ---
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_clean)

# --- Calcular VIF ---
vif_df = pd.DataFrame()
vif_df["Variable"] = df_clean.columns
vif_df["VIF"] = [variance_inflation_factor(X_scaled, i) for i in range(X_scaled.shape[1])]
vif_df = vif_df.sort_values(by="VIF", ascending=False)
print("\n=== VIF ===")
print(vif_df)

# --- Matriz de correlación ---
corr_matrix = df_clean.corr()
plt.figure(figsize=(16, 12))
sns.heatmap(corr_matrix, cmap="coolwarm", annot=False, vmin=-1, vmax=1)
plt.title("Matriz de Correlación (Variables Sociales)")
plt.tight_layout()
plt.savefig("correlacion_social_vars.png", dpi=300)
plt.show()

# Guardar CSV de VIF y correlaciones
vif_df.to_csv("vif_variables_sociales.csv", index=False)
corr_matrix.to_csv("correlacion_social_vars.csv")
