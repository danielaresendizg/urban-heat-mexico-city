import pandas as pd
import numpy as np
from scipy.stats import ttest_ind
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import date

today = date.today().strftime("%Y%m%d")

# Carga tu archivo
file_path = "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/manzanas_IVS_20250724.csv"
df = pd.read_csv(file_path)

groups_dict = {
    "age": ["pct_0a5", "pct_6a14", "pct_15a64", "pct_65plus"],
    "ethnicity": ["pct_ethnic_afro", "pct_ethnic_ind", "pct_ethnic_other"],
    "disability": ["pct_without_disc", "pct_with_disc"],
    "education": ["pct_no_school", "pct_elementary_edu", "pct_elementary2_edu", "pct_more_edu"],
    "economy": ["pct_ocup", "pct_desocup", "pct_inac"],
    "health": ["pct_serv_med", "pct_no_serv_med"],
    "mobility": ["pct_pop_auto", "pct_pop_sin_auto"],
}

def cross_percentile_analysis(df, social_var, thermal_var, q=10, alpha=0.05):
    try:
        df[f"{thermal_var}_group"] = pd.qcut(
            df[thermal_var], q=q, labels=[f"P{i*100//q}-{(i+1)*100//q}" for i in range(q)]
        )
    except ValueError:
        df[f"{thermal_var}_group"] = pd.cut(
            df[thermal_var], bins=q, labels=[f"P{i*100//q}-{(i+1)*100//q}" for i in range(q)]
        )
    groups = df[f"{thermal_var}_group"].dropna().unique()
    groups = sorted(groups)
    matrix = np.zeros((len(groups), len(groups)))
    for i, g1 in enumerate(groups):
        for j, g2 in enumerate(groups):
            if i < j:
                vals1 = df[df[f"{thermal_var}_group"] == g1][social_var].dropna()
                vals2 = df[df[f"{thermal_var}_group"] == g2][social_var].dropna()
                if len(vals1) > 1 and len(vals2) > 1:
                    stat, p = ttest_ind(vals1, vals2, equal_var=False)
                    if p < alpha:
                        matrix[i, j] = 1
                        matrix[j, i] = 1
    signif_counts = matrix.sum(axis=1)
    return groups, signif_counts

# ----------- Análisis para todos los grupos sociales con Ta_mean ----------------

for group in groups_dict:
    granular_results = {}
    for social_var in groups_dict[group]:
        quintil_labels, counts = cross_percentile_analysis(df, social_var, "Ta_mean", q=10)
        granular_results[social_var] = counts

    df_granular = pd.DataFrame(granular_results, index=quintil_labels)
    df_granular.to_csv(f"granular_heatmap_{group}_{today}.csv")
    print(f"Tabla guardada: granular_heatmap_{group}_{today}.csv")
    print(df_granular)

    plt.figure(figsize=(10, 6))
    ax = sns.heatmap(
        df_granular.T, annot=True, cmap="YlOrRd",
        cbar_kws={'label': 'Significant differences'},
        linewidths=0.5, linecolor='white', vmin=0
    )
    plt.title(f"Significant Differences by Thermal Percentile (granular)\nIndicators: {group}, vs Ta_mean ({today})")
    plt.ylabel("Social indicator")
    plt.xlabel("Percentile (thermal variable)")
    plt.tight_layout()
    plt.savefig(f"granular_heatmap_{group}_{today}.png", dpi=300)
    plt.close()
    print(f"Imagen guardada: granular_heatmap_{group}_{today}.png")
