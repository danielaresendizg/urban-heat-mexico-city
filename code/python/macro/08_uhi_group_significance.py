import pandas as pd
import numpy as np
from scipy.stats import ttest_ind, mannwhitneyu

# 1. Cargar archivo
file_path = "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/manzanas_IVS_20250724.csv"
print(f"Leyendo archivo: {file_path}")
df = pd.read_csv(file_path)
print("Shape:", df.shape)
print("Columnas:", df.columns.tolist())
print("Primeras filas:\n", df.head())

# 2. Chequea y fuerza tipos numéricos
for col in ['UHI_mean', 'Ta_mean']:
    df[col] = pd.to_numeric(df[col], errors='coerce')
print(df[['UHI_mean', 'Ta_mean']].describe())

# 3. Define criterios UHI/non-UHI
df['UHI_group_A'] = df['UHI_mean'].apply(lambda x: 'UHI' if x > 0 else 'non-UHI')
df['UHI_group_B'] = df['Ta_mean'].apply(lambda x: 'UHI' if x >= 26 else 'non-UHI')

# 4. Grupos de variables
group_vars = {
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

def compute_significance_matrix_both(df, group_col, group_vars, zero_threshold=0.9, min_n=10):
    signif_ttest = {}
    signif_mw = {}

    df_UHI = df[df[group_col] == 'UHI'].copy()
    df_non = df[df[group_col] == 'non-UHI'].copy()
    print(f"\nFiltrado {group_col}: UHI={df_UHI.shape}, non-UHI={df_non.shape}")

    for g_name, vars_list in group_vars.items():
        signif_ttest[g_name] = {}
        signif_mw[g_name] = {}
        for var in vars_list:
            print(f"\nProcesando grupo: {g_name} | variable: {var}")

            if var not in df.columns:
                print(f"  ❗ Variable {var} NO existe en el DataFrame")
                signif_ttest[g_name][var] = "NA"
                signif_mw[g_name][var] = "NA"
                continue

            data_UHI = pd.to_numeric(df_UHI[var], errors='coerce').dropna()
            data_non = pd.to_numeric(df_non[var], errors='coerce').dropna()
            print(f"  Tamaño muestra: UHI={len(data_UHI)}, non-UHI={len(data_non)}")

            if len(data_UHI) < min_n or len(data_non) < min_n:
                print(f"  ⚠️  Saltando {var}: muestra demasiado pequeña.")
                signif_ttest[g_name][var] = "NA"
                signif_mw[g_name][var] = "NA"
                continue

            frac_zero_UHI = (data_UHI == 0).mean()
            frac_zero_non = (data_non == 0).mean()
            if frac_zero_UHI > zero_threshold:
                print(f"  ⚠️  >{int(zero_threshold*100)}% ceros en UHI ({frac_zero_UHI:.1%})")
            if frac_zero_non > zero_threshold:
                print(f"  ⚠️  >{int(zero_threshold*100)}% ceros en non-UHI ({frac_zero_non:.1%})")

            try:
                t, p_ttest = ttest_ind(data_UHI, data_non, equal_var=False)
                signif_ttest[g_name][var] = "Yes" if p_ttest < 0.05 else "No"
                print(f"    t-test: p={p_ttest:.4f} ({'Yes' if p_ttest<0.05 else 'No'})")
            except Exception as e:
                print(f"    Error t-test: {e}")
                signif_ttest[g_name][var] = "NA"
            try:
                u, p_mw = mannwhitneyu(data_UHI, data_non, alternative='two-sided')
                signif_mw[g_name][var] = "Yes" if p_mw < 0.05 else "No"
                print(f"    Mann-Whitney U: p={p_mw:.4f} ({'Yes' if p_mw<0.05 else 'No'})")
            except Exception as e:
                print(f"    Error Mann-Whitney: {e}")
                signif_mw[g_name][var] = "NA"
    return pd.DataFrame(signif_ttest), pd.DataFrame(signif_mw)

# 5. Ejecuta para ambos criterios
print("Criterio A (UHI_mean > 0):")
signif_A_t, signif_A_mw = compute_significance_matrix_both(df, 'UHI_group_A', group_vars)
print("t-test:\n", signif_A_t)
print("Mann-Whitney U:\n", signif_A_mw)

print("\nCriterio B (Ta_mean >= 26):")
signif_B_t, signif_B_mw = compute_significance_matrix_both(df, 'UHI_group_B', group_vars)
print("t-test:\n", signif_B_t)
print("Mann-Whitney U:\n", signif_B_mw)

# 6. Exporta resultados
signif_A_t.to_csv("significancia_UHI_mean_ttest.csv")
signif_A_mw.to_csv("significancia_UHI_mean_mw.csv")
signif_B_t.to_csv("significancia_Ta26_ttest.csv")
signif_B_mw.to_csv("significancia_Ta26_mw.csv")

# 7. Visualización tipo heatmap (con paleta YlOrRd, resolución 400 dpi)
import seaborn as sns
import matplotlib.pyplot as plt

def plot_heatmap(matrix, title, fname=None):
    # Rellena NaN por "No" (puedes usar "NA" si lo prefieres)
    matrix = matrix.copy().fillna("No")
    matrix_bool = matrix.replace({"Yes":1, "No":0, "NA":np.nan})
    # Asegura el mismo shape/orientación de datos y anotaciones
    matrix_bool = matrix_bool.reindex_like(matrix)
    cmap = sns.color_palette("YlOrRd", as_cmap=True)
    plt.figure(figsize=(12,4))
    # Transpone ambos (matrix.T) para tener variables en eje Y y grupos en X, igual que tus tablas
    ax = sns.heatmap(
        matrix_bool.T, annot=matrix.T, cmap=cmap,
        cbar=False, linewidths=.5, linecolor='white',
        annot_kws={"size":14}, fmt='', 
        vmin=0, vmax=1
    )
    plt.title(title)
    plt.xlabel("Grupo")
    plt.ylabel("Variable")
    plt.tight_layout()
    if fname:
        plt.savefig(fname, dpi=400)
    plt.show()

# Llama la función para cada matriz:
plot_heatmap(signif_A_t, "Significancia t-test (media urbana)", "heatmap_UHI_mean_ttest.png")
plot_heatmap(signif_A_mw, "Significancia Mann-Whitney (media urbana)", "heatmap_UHI_mean_mw.png")
plot_heatmap(signif_B_t, "Significancia t-test (umbral 26°C)", "heatmap_Ta26_ttest.png")
plot_heatmap(signif_B_mw, "Significancia Mann-Whitney (umbral 26°C)", "heatmap_Ta26_mw.png")
