import pandas as pd
import numpy as np
from itertools import combinations
from scipy.stats import ttest_ind
import matplotlib.pyplot as plt
import seaborn as sns

# --------------- PARTE 1: Análisis estadístico de diferencias significativas -------------------

# Ruta de tu archivo
file_path = "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/manzanas_IVS_20250724.csv"
df = pd.read_csv(file_path)

# Variables sociales y térmicas (ajusta si tus columnas tienen otro nombre)
social_vars = [
    "pct_0a5", "pct_6a14", "pct_15a64", "pct_65plus", "pct_ethnic_afro", 
    "pct_ethnic_ind", "pct_ethnic_other", "pct_without_disc", "pct_with_disc", 
    "pct_no_school", "pct_elementary_edu", "pct_elementary2_edu", "pct_more_edu", 
    "pct_ocup", "pct_desocup", "pct_inac", "pct_serv_med", "pct_no_serv_med", 
    "pct_pop_auto", "pct_pop_sin_auto", "rel_dependencia_0_14", "rel_h_m"

]
thermal_vars = [
    "Ta_mean", "Ta_max", "LST_mean", "Albedo_mean", "NDVI_mean",
    "NDBI_mean", "UHI_mean", "UHI_max"
]

summary = []

for thermal_var in thermal_vars:
    if thermal_var not in df.columns:
        print(f"Variable térmica no encontrada y será ignorada: {thermal_var}")
        continue
    for social_var in social_vars:
        if social_var not in df.columns:
            print(f"Variable social no encontrada y será ignorada: {social_var}")
            continue
        try:
            df['quintil_social'] = pd.qcut(df[social_var], 5, labels=[1,2,3,4,5])
        except ValueError:
            print(f"Advertencia: no se pudo calcular quintiles para {social_var} (valores repetidos)")
            continue

        groups = df['quintil_social'].dropna().unique()
        significant_counts = {g: 0 for g in groups}
        for g1, g2 in combinations(groups, 2):
            vals1 = df[df['quintil_social'] == g1][thermal_var].dropna()
            vals2 = df[df['quintil_social'] == g2][thermal_var].dropna()
            if len(vals1) > 10 and len(vals2) > 10:
                t, p = ttest_ind(vals1, vals2, equal_var=False)
                if p < 0.05:
                    significant_counts[g1] += 1
                    significant_counts[g2] += 1
        for g in groups:
            summary.append({
                'thermal_var': thermal_var,
                'social_var': social_var,
                'quintil': g,
                'n_significant_differences': significant_counts[g]
            })

# Tabla de resultados lista para heatmap
summary_df = pd.DataFrame(summary)

# Suma de diferencias significativas por variable social y térmica
heatmap_data = summary_df.groupby(['social_var', 'thermal_var'])['n_significant_differences'].sum().unstack()

# Orden amigable para variables (opcional)
pretty_names = {
"pct_0a5": "%_0a5",
"pct_6a14": "%_6a14",
"pct_15a64": "%_15a64",
"pct_65plus": "%_65plus",
"pct_ethnic_afro": "%_ethnic_afro",
"pct_ethnic_ind": "%_ethnic_ind",
"pct_ethnic_other": "%_ethnic_other",
"pct_without_disc": "%_without_disc",
"pct_with_disc": "%_with_disc",
"pct_no_school": "%_no_school",
"pct_elementary_edu": "%_elementary_edu",
"pct_elementary2_edu": "%_elementary2_edu",
"pct_more_edu": "%_more_edu",
"pct_ocup": "%_ocup",
"pct_desocup": "%_desocup",
"pct_inac": "%_inac",
"pct_serv_med": "%_serv_med",
"pct_no_serv_med": "%_no_serv_med",
"pct_pop_auto": "%_pop_auto",
"pct_pop_sin_auto": "%_pop_sin_auto",
"rel_dependencia_0_14": "%_dependencia_0_14",
"rel_h_m": "%_h_m"
}
heatmap_data.index = [pretty_names.get(i, i) for i in heatmap_data.index]

# Opcional: ordena variables térmicas (ajusta al orden que desees)
thermal_order = [col for col in thermal_vars if col in heatmap_data.columns]
heatmap_data = heatmap_data[thermal_order]

# Guarda la tabla resultado para uso posterior
heatmap_data.to_excel("tabla_heatmap_significancia.quintiles.xlsx")

# --------------- PARTE 2: Visualización-------------------

plt.figure(figsize=(10, 11), dpi=300)
sns.set(font_scale=1.2, style="whitegrid")
cmap = sns.color_palette("YlOrRd", as_cmap=True)

ax = sns.heatmap(
    heatmap_data,
    cmap=cmap,
    annot=True,
    fmt=".0f",
    linewidths=0.7,
    linecolor='grey',
    cbar_kws={"label": "No. diferencias significativas"},
    square=False
)

plt.xlabel("Variable térmica", fontsize=15, labelpad=18)
plt.ylabel("Indicador social", fontsize=15, labelpad=18)
plt.title("Diferencias significativas entre quintiles\npor indicador social y variable térmica", fontsize=17, pad=20)
plt.xticks(fontsize=12, rotation=30, ha='right')
plt.yticks(fontsize=12)
plt.tight_layout(rect=[0, 0, 1, 0.98])
plt.savefig("heatmap_dif_signif_vulnerabilidad.quintiles.png", dpi=400)
plt.show()

print("✅ ¡Listo! Tabla y heatmap generados en el directorio actual.")
