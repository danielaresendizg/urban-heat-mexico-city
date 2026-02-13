import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from esda.moran import Moran_Local_BV
from libpysal.weights import KNN
import statsmodels.api as sm
import os
import pandas as pd
from datetime import datetime
from matplotlib.patches import Patch
import matplotlib.font_manager as fm

# --- Configuración de salidas ---
fecha = datetime.now().strftime('%Y%m%d')
output_dir = f'output_{fecha}'
os.makedirs(output_dir, exist_ok=True)
os.makedirs(f'{output_dir}/lisa', exist_ok=True)
os.makedirs(f'{output_dir}/regression', exist_ok=True)
os.makedirs(f'{output_dir}/maps', exist_ok=True)
os.makedirs(f'{output_dir}/tables', exist_ok=True)

# --- Cargar datos ---
gdf = gpd.read_file('/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/manzanas_IVS_20250724.gpkg')

# Variables sociales y térmicas
social_vars = ["pct_0a5", "pct_6a14", "pct_15a64", "pct_65plus", "pct_ethnic_afro", 
    "pct_ethnic_ind", "pct_ethnic_other", "pct_without_disc", "pct_with_disc", 
    "pct_no_school", "pct_elementary_edu", "pct_elementary2_edu", "pct_more_edu", 
    "pct_ocup", "pct_desocup", "pct_inac", "pct_serv_med", "pct_no_serv_med", 
    "pct_pop_auto", "pct_pop_sin_auto", "rel_dependencia_0_14", "rel_h_m"]
thermal_vars = ['Ta_mean']

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
        gdf_sub['lisa_type'] = lisa.q

        def cluster_label(row):
            if not row['lisa_sig']:
                return 'Not significant'
            if row['lisa_type'] == 1:
                return 'High-High'
            if row['lisa_type'] == 2:
                return 'Low-High'
            if row['lisa_type'] == 3:
                return 'Low-Low'
            if row['lisa_type'] == 4:
                return 'High-Low'
            return 'Not significant'

        gdf_sub['cluster'] = gdf_sub.apply(cluster_label, axis=1)

        cluster_colors = {
            'High-High': '#e41a1c',     # Rojo
            'Low-Low':   '#377eb8',     # Azul
            'Low-High':  '#a6cee3',     # Celeste
            'High-Low':  '#fbb4ae',     # Rosa claro
            'Not significant': '#eeeeee' # Gris muy claro
        }
        legend_order = ['High-High', 'Low-Low', 'Low-High', 'High-Low', 'Not significant']

        # Conteo de cada categoría
        cluster_counts = gdf_sub['cluster'].value_counts().reindex(legend_order, fill_value=0)
        cluster_legend = [f"{lab} ({cluster_counts[lab]})" for lab in legend_order]

        # Calcular medias
        mean_soc = gdf_sub[soc].mean()
        mean_therm = gdf_sub[therm].mean()

        fig, ax = plt.subplots(1, 1, figsize=(10, 10))
        gdf_sub.plot(
            ax=ax,
            column='cluster',
            legend=False,
            alpha=0.95,
            edgecolor='white',
            linewidth=0.05,
            color=gdf_sub['cluster'].map(cluster_colors)
        )

        # Leyenda con fuente pequeña y elegante
        legend_elements = [
            Patch(facecolor=cluster_colors[lab], edgecolor='white', label=lab_str)
            for lab, lab_str in zip(legend_order, cluster_legend)
        ]
        legend_font = fm.FontProperties(size=9)  # Tamaño de fuente de leyenda
        ax.legend(
            handles=legend_elements,
            title='Clusters',
            loc='lower left',
            prop=legend_font,
            title_fontsize=10,
            frameon=True,
            framealpha=0.95,
            borderpad=0.8,
            handlelength=1.5,
            handletextpad=0.5
        )

        # Medias en la esquina
        ax.annotate(
            f"Media {soc}: {mean_soc:.2f}\nMedia {therm}: {mean_therm:.2f}",
            xy=(0.01, 0.99),
            xycoords='axes fraction',
            fontsize=14,
            ha='left', va='top',
            bbox=dict(boxstyle='round', fc='white', alpha=0.8, ec='gray')
        )

        ax.set_title(f'LISA Bivariado: {soc} vs {therm}', fontsize=16)
        ax.axis('off')

        for ext in ['png']:
            plt.savefig(f'{output_dir}/lisa/lisa_{soc}_{therm}_paperstyle.{ext}', bbox_inches='tight', dpi=300)
        gdf_sub.to_file(f'{output_dir}/lisa/lisa_{soc}_{therm}_paperstyle.gpkg', driver='GPKG')
        plt.close()


