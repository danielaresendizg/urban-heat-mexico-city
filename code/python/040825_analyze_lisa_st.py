import geopandas as gpd
import numpy as np
from esda.moran import Moran_Local_BV
from libpysal.weights import KNN
import pandas as pd
from datetime import datetime
import os

# --- Configuración de salidas ---
fecha = datetime.now().strftime('%Y%m%d')
output_dir = f'output_{fecha}'
os.makedirs(output_dir, exist_ok=True)
os.makedirs(f'{output_dir}/tables', exist_ok=True)

# --- Cargar datos ---
gdf = gpd.read_file('/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/manzanas_IVS_20250724.gpkg')

social_vars = [
    "pct_0a5", "pct_6a14", "pct_15a64", "pct_65plus", "pct_ethnic_afro", 
    "pct_ethnic_ind", "pct_ethnic_other", "pct_without_disc", "pct_with_disc", 
    "pct_no_school", "pct_elementary_edu", "pct_elementary2_edu", "pct_more_edu", 
    "pct_ocup", "pct_desocup", "pct_inac", "pct_serv_med", "pct_no_serv_med", 
    "pct_pop_auto", "pct_pop_sin_auto", "rel_dependencia_0_14", "rel_h_m"
]
thermal_vars = ['Ta_mean']

moran_results = []

for soc in social_vars:
    for therm in thermal_vars:
        if soc not in gdf.columns or therm not in gdf.columns:
            print(f"Variable faltante: {soc} o {therm}, se omite combinación.")
            continue
        gdf_sub = gdf[[soc, therm, 'geometry']].dropna()
        if gdf_sub.empty or len(gdf_sub) < 3:
            print(f"Sin datos para {soc} vs {therm}, se omite combinación.")
            continue
        gdf_sub = gdf_sub[gdf_sub.is_valid]
        try:
            w = KNN.from_dataframe(gdf_sub, k=4)
        except Exception as e:
            print(f"No se pudo construir matriz KNN para {soc} vs {therm}: {e}")
            continue
        w.transform = 'r'
        lisa = Moran_Local_BV(gdf_sub[soc], gdf_sub[therm], w)
        gdf_sub['lisa_sig'] = lisa.p_sim < 0.05

        # Calcula Global Moran’s I como la media de los valores locales
        global_I = np.mean(lisa.Is)
        # Otros atributos: si no existen, pon NA
        try:
            expected = lisa.EI_sim
        except AttributeError:
            expected = 'NA'
        try:
            variance = lisa.VI_sim
        except AttributeError:
            variance = 'NA'
        try:
            zscore = lisa.z_sim
        except AttributeError:
            zscore = 'NA'
        try:
            pvalue = lisa.p_z_sim
        except AttributeError:
            pvalue = 'NA'

        moran_results.append({
            'Variable': soc,
            'Thermal': therm,
            'Global Moran’s I (mean local)': global_I,
            'Expected': expected,
            'Variance': variance,
            'z-score': zscore,
            'p-value': pvalue,
            'Local Min': lisa.Is.min(),
            'Local Max': lisa.Is.max(),
            'Local Mean': lisa.Is.mean(),
            'Local SD': lisa.Is.std(),
            'Local % Significance': gdf_sub['lisa_sig'].mean() * 100,
            'N': len(gdf_sub)
        })

tabla_moran = pd.DataFrame(moran_results)
tabla_moran.to_csv(f'{output_dir}/tables/lisa_global_local_stats.csv', index=False)
print("Tabla de Moran's I global/local guardada en:", f'{output_dir}/tables/lisa_global_local_stats.csv')
print(tabla_moran)
