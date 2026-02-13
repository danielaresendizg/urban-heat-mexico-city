import geopandas as gpd
import pandas as pd
import numpy as np
import os
from mgwr.gwr import GWR
from mgwr.sel_bw import Sel_BW
from mgwr.utils import shift_colormap

# === Configuración ===
input_path = "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/manzanas_IVS_20250724_con_alcaldia.gpkg"
output_dir = "evaluacion_variables_GWR"
os.makedirs(output_dir, exist_ok=True)
output_txt = os.path.join(output_dir, "informe_variables.txt")
output_csv = os.path.join(output_dir, "resumen_variables.csv")
output_corr = os.path.join(output_dir, "correlaciones_variables.csv")
output_bw = os.path.join(output_dir, "bandwidth_optimo.txt")

# === Cargar datos ===
gdf = gpd.read_file(input_path)
cols = gdf.columns

# --- Identificar variables sociales (proporciones) ---
social_prefixes = ['pct_', 'prop_']
social_vars = [c for c in cols if any([c.startswith(pref) for pref in social_prefixes])]
social_vars = sorted(list(set(social_vars)))
if 'personas_sin_auto' in cols:
    social_vars.append('personas_sin_auto')

# --- Variables térmicas ---
thermal_vars = [c for c in ['Ta_mean', 'Ta_max', 'LST_mean', 'UHI_mean', 'NDVI_mean'] if c in cols]

# --- Estadísticos descriptivos y ceros ---
res = []
for v in social_vars + thermal_vars:
    x = gdf[v]
    num_total = len(x)
    num_ceros = (x == 0).sum()
    num_nulos = x.isna().sum()
    num_unicos = x.nunique()
    minv, maxv, meanv, stdv = x.min(), x.max(), x.mean(), x.std()
    pct_ceros = 100 * num_ceros / num_total
    res.append({
        'variable': v,
        'n_total': num_total,
        'n_ceros': num_ceros,
        'pct_ceros': pct_ceros,
        'n_nulos': num_nulos,
        'n_unicos': num_unicos,
        'min': minv, 'max': maxv, 'mean': meanv, 'std': stdv,
    })

res_df = pd.DataFrame(res)

# --- Análisis extendido: cuántos valores >0 por variable social ---
extendido = []
for v in social_vars:
    x = gdf[v]
    n_gt0 = (x > 0).sum()
    pct_gt0 = 100 * n_gt0 / len(x)
    extendido.append({
        'variable': v,
        'n_gt0': n_gt0,
        'pct_gt0': pct_gt0,
    })
extendido_df = pd.DataFrame(extendido)
res_df = pd.merge(res_df, extendido_df, on='variable', how='left')

# --- Correlaciones ---
corr_vars = [v for v in social_vars + thermal_vars if gdf[v].dtype != object]
corr_matrix = gdf[corr_vars].corr()

# --- Evaluación de variables útiles para GWR ---
def variable_ok(row):
    if row['n_unicos'] < 3: return False
    if row['pct_ceros'] > 95: return False
    if abs(row['mean']) > 0 and abs(row['std']) / abs(row['mean']) < 0.05: return False
    if 'pct_gt0' in row and row['pct_gt0'] is not None and row['pct_gt0'] < 1: return False
    return True

res_df['candidata_GWR'] = res_df.apply(variable_ok, axis=1)

# --- Diagnóstico adicional de variabilidad para variables sociales ---
problematicas = []
for v in social_vars:
    x = gdf[v]
    pct_ceros = 100 * (x == 0).sum() / len(x)
    std = x.std()
    if pct_ceros > 99:
        problematicas.append((v, f"⚠️ Más de 99% ceros ({pct_ceros:.2f}%)"))
    elif std < 0.01:
        problematicas.append((v, f"⚠️ Desviación estándar muy baja ({std:.4f})"))
if len(problematicas) > 0:
    print("\n=== ADVERTENCIA: Variables sociales potencialmente problemáticas para GWR ===")
    for v, msg in problematicas:
        print(f" - {v}: {msg}")
else:
    print("\nTodas las variables sociales tienen variabilidad aceptable.")

# --- Guardar resultados CSV ---
res_df.to_csv(output_csv, index=False)
corr_matrix.to_csv(output_corr)

# --- Selección de variable para estimar bandwidth (puedes cambiar aquí) ---
var_dep = 'Ta_max'          # Variable dependiente
var_control = 'NDVI_mean'   # Control
var_social = 'pct_SE_pri'   # Candidata social

# --- Muestreo para cálculo de bandwidth ---
N = 3000
gdf_bw = gdf.dropna(subset=[var_dep, var_control, var_social])
if len(gdf_bw) > N:
    gdf_bw = gdf_bw.sample(N, random_state=42)

# --- Prepara variables para mgwr ---
centroids = gdf_bw.geometry.centroid
coords = np.column_stack((centroids.x, centroids.y))
y = gdf_bw[[var_dep]].values
X = gdf_bw[[var_control, var_social]].values

# --- Cálculo del bandwidth óptimo ---
bw_opt = None
if len(gdf_bw) >= 100:  # mínimo de casos para que tenga sentido
    selector = Sel_BW(coords, y, X, spherical=True)
    bw_opt = selector.search(bw_min=40)
    with open(output_bw, 'w') as f:
        f.write(f"Bandwidth óptimo para modelo {var_dep} ~ {var_control} + {var_social} (muestra n={len(gdf_bw)}): {bw_opt}\n")
    print(f"\n✔️ Bandwidth óptimo estimado: {bw_opt} (modelo: {var_dep} ~ {var_control} + {var_social}, muestra n={len(gdf_bw)})")
else:
    with open(output_bw, 'w') as f:
        f.write("⚠️ No hay suficientes observaciones para estimar bandwidth óptimo en la muestra.\n")
    print("⚠️ No hay suficientes observaciones para estimar bandwidth óptimo.")

# --- Informe TXT ---
with open(output_txt, 'w', encoding='utf-8') as f:
    f.write("=== Evaluación de Variables para GWR ===\n\n")
    f.write("Archivo evaluado: %s\n\n" % input_path)
    f.write("Variables térmicas:\n%s\n\n" % ", ".join(thermal_vars))
    f.write("Variables sociales/proporciones:\n%s\n\n" % ", ".join(social_vars))
    f.write("Resumen de cada variable:\n")
    f.write(res_df.to_string(index=False))
    f.write("\n\n--- Resumen de valores >0 por variable social ---\n")
    f.write(extendido_df.to_string(index=False))
    f.write("\n")
    f.write("\n--- Diagnóstico adicional de variabilidad ---\n")
    if len(problematicas) > 0:
        for v, msg in problematicas:
            f.write(f"{v}: {msg}\n")
    else:
        f.write("Todas las variables sociales tienen variabilidad aceptable.\n")
    f.write("\n--- Correlación entre variables (Pearson) ---\n")
    f.write(corr_matrix.round(3).to_string())
    f.write("\n\nVariables sugeridas para GWR:\n")
    candidatas = res_df[res_df['candidata_GWR']]['variable'].tolist()
    f.write(", ".join(candidatas))
    f.write("\n\nVariables NO sugeridas (constantes, sin variabilidad, demasiados ceros, o con <1% >0):\n")
    no_candidatas = res_df[~res_df['candidata_GWR']]['variable'].tolist()
    f.write(", ".join(no_candidatas))
    f.write("\n")
    # --- Bandwidth óptimo ---
    if bw_opt:
        f.write(f"\n--- Bandwidth óptimo para modelo {var_dep} ~ {var_control} + {var_social}: {bw_opt} (n={len(gdf_bw)}) ---\n")
    else:
        f.write("\n--- Bandwidth óptimo no estimado por falta de datos suficientes ---\n")

print(f"\n✅ Revisión completa. Archivos generados en: {output_dir}")
print(f"- Informe TXT: {output_txt}")
print(f"- Resumen CSV: {output_csv}")
print(f"- Correlaciones: {output_corr}")
print(f"- Bandwidth óptimo: {output_bw}")
