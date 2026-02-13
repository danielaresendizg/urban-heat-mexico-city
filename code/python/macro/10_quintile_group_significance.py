import pandas as pd
import numpy as np
import itertools
from scipy.stats import ttest_ind
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import date

today = date.today().strftime("%Y%m%d")

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
    "care": ["rel_dependencia_0_14"],
    "gender": ["rel_h_m"]
}
thermal_vars = ["Ta_mean"]

def summary_statistical_analysis(df, social_vars, thermal_var, alpha=0.05, q=5):
    results = {}
    for var in social_vars:
        try:
            df[f"{var}_group"] = pd.qcut(df[var], q=q, labels=[f"Q{i+1}" for i in range(q)])
        except ValueError:
            df[f"{var}_group"] = pd.cut(df[var], bins=q, labels=[f"Q{i+1}" for i in range(q)])
        groups = df[f"{var}_group"].dropna().unique()
        groups = sorted(groups)
        combos = list(itertools.combinations(groups, 2))
        significant = 0
        for g1, g2 in combos:
            vals1 = df[df[f"{var}_group"] == g1][thermal_var].dropna()
            vals2 = df[df[f"{var}_group"] == g2][thermal_var].dropna()
            if len(vals1) > 1 and len(vals2) > 1:
                stat, p = ttest_ind(vals1, vals2, equal_var=False)
                if p < alpha:
                    significant += 1
        results[var] = significant
    return results

all_results = {}
for group, social_vars in groups_dict.items():
    for thermal_var in thermal_vars:
        res = summary_statistical_analysis(df, social_vars, thermal_var, q=5)
        for var, count in res.items():
            all_results[(group, var, thermal_var)] = count

rows = []
row_index = []
for group, social_vars in groups_dict.items():
    for var in social_vars:
        row = []
        for thermal_var in thermal_vars:
            row.append(all_results.get((group, var, thermal_var), np.nan))
        rows.append(row)
        row_index.append(f"{group}_{var}")

result_table = pd.DataFrame(rows, index=row_index, columns=thermal_vars)

result_table.to_csv(f"significance_summary_quintiles_{today}.csv")
print(f"Tabla guardada en significance_summary_quintiles_{today}.csv")
print(result_table)

plt.figure(figsize=(12,8))
ax = sns.heatmap(result_table, annot=True, cmap=sns.color_palette("YlOrRd", as_cmap=True),
            cbar_kws={'label': 'Significant differences'},
            linewidths=1, linecolor='white', vmin=0, vmax=10)
group_lengths = [len(sv) for sv in groups_dict.values()]
sep_idx = np.cumsum(group_lengths)[:-1]
for i in sep_idx:
    ax.hlines(i, *ax.get_xlim(), colors='black', linewidth=2)
plt.title(f"Significant differences by quintile (summary)\nSocial Indicator Quintiles vs Ta_mean ({today})", fontsize=16)
plt.ylabel("Social indicator (quintiles)")
plt.xlabel("Group (variable)")
plt.tight_layout()
plt.savefig(f"significance_heatmap_quintiles_{today}_kimoncolors.png", dpi=400)
plt.show()
print(f"Imagen guardada en significance_heatmap_quintiles_{today}.png")
