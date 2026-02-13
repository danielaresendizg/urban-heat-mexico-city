#!/usr/bin/env python3
#!/usr/bin/env python3
"""
generate_figures.py

Genera las figuras propuestas para el informe consultor:
1) Mapa coroplético de IVS
2) Boxplot de IVS por alcaldía
3) Histograma + densidad de IVS
4) Small multiples de mapas Top30 por indicador
5) Heatmap de correlación
6) Scatter vul_PRO_OCUP_C vs vul_GRAPROES

Guarda cada figura en PNG, PDF y SVG en la carpeta 'figures' e imprime un resumen de los archivos generados.
"""
import os
import argparse
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns  # solo para el kdeplot

# Argumentos
def parse_args():
    parser = argparse.ArgumentParser(description="Genera figuras del IVS para informe")
    parser.add_argument("--input", help="CSV de salida con columnas IVS y variables", required=True)
    parser.add_argument("--gpkg",  help="GeoPackage con geometrías (capa manzanas)", required=True)
    parser.add_argument("--outdir", help="Carpeta salida figuras", default="figures")
    return parser.parse_args()

# Asegura carpeta
def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# 1) Mapa coroplético de IVS

def plot_choropleth_ivss(gdf, outdir):
    fig, ax = plt.subplots(figsize=(10, 8))
    # Usamos plot simple sin 'scheme' para evitar dependencia de mapclassify
    gdf.plot(column='IVS_decile', cmap='OrRd', legend=True,
             ax=ax, linewidth=0, edgecolor='none')
    ax.set_axis_off()
    ax.set_title('IVS CDMX por decil', fontsize=14)
    for fmt in ['png', 'pdf', 'svg']:
        fig.savefig(os.path.join(outdir, f'1_choropleth_IVS.{fmt}'), dpi=300, bbox_inches='tight')
    plt.close(fig)

# 2) Boxplot de IVS por alcaldía

def plot_box_ivss(gdf, outdir):
    df = gdf[['ALCALDIA', 'IVS']].dropna()
    order = df.groupby('ALCALDIA').median().sort_values('IVS').index
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(x='ALCALDIA', y='IVS', data=df, order=order, ax=ax)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    ax.set_title('Distribución de IVS por alcaldía', fontsize=12)
    fig.tight_layout()
    for fmt in ['png', 'pdf', 'svg']:
        fig.savefig(os.path.join(outdir, f'2_boxplot_IVS_alcaldia.{fmt}'), dpi=300)
    plt.close(fig)

# 3) Histograma + densidad de IVS

def plot_hist_kde_ivss(gdf, outdir):
    ivs = gdf['IVS'].dropna()
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.histplot(ivs, bins=30, kde=False, stat='density', ax=ax)
    sns.kdeplot(ivs, ax=ax)
    ax.set_title('Histograma y densidad de IVS', fontsize=12)
    ax.set_xlabel('IVS')
    fig.tight_layout()
    for fmt in ['png', 'pdf', 'svg']:
        fig.savefig(os.path.join(outdir, f'3_hist_kde_IVS.{fmt}'), dpi=300)
    plt.close(fig)

# 4) Small multiples de mapas Top30

def plot_small_multiples_top30(gdf, prop_vars, outdir):
    n = len(prop_vars)
    cols = 3
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(cols*5, rows*5))
    axes = axes.flatten()
    for i, name in enumerate(prop_vars):
        ax = axes[i]
        gdf[gdf[f'top30_{name}']].plot(ax=ax, color='red', markersize=1)
        ax.set_title(f'Top30 {name}')
        ax.set_axis_off()
    for j in range(i+1, rows*cols):
        axes[j].set_axis_off()
    fig.tight_layout()
    for fmt in ['png', 'pdf', 'svg']:
        fig.savefig(os.path.join(outdir, f'4_small_multiples_top30.{fmt}'), dpi=300)
    plt.close(fig)

# 5) Heatmap de correlación

def plot_heatmap_corr(df, outdir):
    # Seleccionar solo columnas numéricas para evitar errores de conversión
    num_df = df.select_dtypes(include='number')
    corr = num_df.corr()
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, mask=corr.abs() < 0.2, annot=True, fmt='.2f', ax=ax)
    ax.set_title('Heatmap correlacional (|r| > 0.2)')
    fig.tight_layout()
    for fmt in ['png', 'pdf', 'svg']:
        fig.savefig(os.path.join(outdir, f'5_heatmap_corr.{fmt}'), dpi=300)
    plt.close(fig)

# 6) Scatter vul_PRO_OCUP_C vs vul_GRAPROES

def plot_scatter_vul(df, outdir):
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.scatterplot(x='vul_PRO_OCUP_C', y='vul_GRAPROES', hue='IVS_cat3',
                    palette='Set2', data=df, ax=ax)
    ax.set_title('vul_PRO_OCUP_C vs vul_GRAPROES')
    fig.tight_layout()
    for fmt in ['png', 'pdf', 'svg']:
        fig.savefig(os.path.join(outdir, f'6_scatter_vul.{fmt}'), dpi=300)
    plt.close(fig)

# Imprime resumen de archivos generados

def print_summary():
    print("\nResumen de archivos generados:")
    print("| Nº | Gráfico                                                | Archivos generados                                                               |")
    print("| -- | ------------------------------------------------------ | -------------------------------------------------------------------------------- |")
    print("| 1  | **Mapa coroplético de IVS por decil**                  | `1_choropleth_IVS.png`  <br> `1_choropleth_IVS.pdf`  <br> `1_choropleth_IVS.svg` |")
    print("| 2  | **Boxplot de IVS por alcaldía**                        | `2_boxplot_IVS_alcaldia.png`  <br> `2_boxplot_IVS_alcaldia.pdf`  <br> `2_boxplot_IVS_alcaldia.svg` |")
    print("| 3  | **Histograma + densidad de IVS**                       | `3_hist_kde_IVS.png`  <br> `3_hist_kde_IVS.pdf`  <br> `3_hist_kde_IVS.svg`       |")
    print("| 4  | **Small multiples: mapas Top 30 % de cada proporción** | `4_small_multiples_top30.png`  <br> `4_small_multiples_top30.pdf`  <br> `4_small_multiples_top30.svg` |")
    print("| 5  | **Heatmap de correlación (|r| > 0.2)**                 | `5_heatmap_corr.png`  <br> `5_heatmap_corr.pdf`  <br> `5_heatmap_corr.svg`       |")
    print("| 6  | **Scatter de vul_PRO_OCUP_C vs vul_GRAPROES**          | `6_scatter_vul.png`  <br> `6_scatter_vul.pdf`  <br> `6_scatter_vul.svg`         |" )

# Main
def main():
    args = parse_args()
    ensure_dir(args.outdir)
    df  = pd.read_csv(args.input)
    gdf = gpd.read_file(args.gpkg, layer='manzanas')

    plot_choropleth_ivss(gdf, args.outdir)
    plot_box_ivss(gdf, args.outdir)
    plot_hist_kde_ivss(gdf, args.outdir)
    prop_list = [c for c in df.columns if c.startswith('pct_')]
    plot_small_multiples_top30(gdf, prop_list, args.outdir)
    plot_heatmap_corr(df, args.outdir)
    plot_scatter_vul(df, args.outdir)
    print_summary()

if __name__ == '__main__':
    main()

