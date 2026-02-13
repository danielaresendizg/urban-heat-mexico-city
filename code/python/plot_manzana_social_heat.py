# plot_manzana_social_heat.py
# ---------------------------
# Genera scatter y mapas bivariados Ta_max vs variables sociales
# usando únicamente la capa de manzana en tu GPkg (sin shapefile externo).

import sys
from pathlib import Path

import geopandas as gpd
import fiona
import matplotlib.pyplot as plt
import seaborn as sns
import contextily as cx

# —————————————————————————————————————————————————————————————————————
# CONFIGURACIÓN de rutas
HOME       = Path.home() / "Library/CloudStorage" / \
             "OneDrive-UniversityCollegeLondon(2)" / "Dissertation" / "01_data"

GPKG_FILE  = HOME / "01_Manzana" / "manzana_thermal-IVS.gpkg"

TARGETS    = ['IZTAPALAPA','GUSTAVO A. MADERO','VENUSTIANO CARRANZA']

VARS       = [
    'IVS',
    'pct_014', 'pct_60plus', 'pct_hli', 'pct_afro',
    'pct_disc', 'pct_inac', 'GRAPROES', 'PRO_OCUP_C'
]
LABELS     = {
    'IVS':         'Índice de Vulnerabilidad Social',
    'pct_014':     '% población 0–14 años',
    'pct_60plus':  '% población ≥60 años',
    'pct_hli':     '% viviendas sin infraestructura',
    'pct_afro':    '% población afrodesc.',
    'pct_disc':    '% población con discapacidad',
    'pct_inac':    '% población inactiva',
    'GRAPROES':    '% población sin escolaridad',
    'PRO_OCUP_C':  '% población ocupada'
}

QT_TA      = 0.90   # percentil para "calor alto"
QT_VAR     = 0.70   # percentil para "variable alta"

COL_TA     = 'Ta_max'  # columna temperatura
COL_ALC    = 'ALC'     # columna alcaldía aproximada

# Carpeta de salida
OUT_DIR    = Path.cwd() / "figures_median_scale"
# —————————————————————————————————————————————————————————————————————

def main():
    # Crear carpeta de salida
    OUT_DIR.mkdir(exist_ok=True)
    print(f"> Carpeta de figuras: {OUT_DIR.resolve()}")

    # Verifica GPkg
    if not GPKG_FILE.exists():
        print(f"ERROR: No encontré GPkg en {GPKG_FILE}", file=sys.stderr)
        sys.exit(1)

    # Lista y lee capa del GPkg
    layers = fiona.listlayers(str(GPKG_FILE))
    print("Capas en GPkg:", layers)
    gdf = gpd.read_file(GPKG_FILE, layer=layers[0])
    print(f"Manzanas cargadas: {len(gdf)}")

    # Detecta columna de alcaldía si 'ALC' no existe
    if COL_ALC not in gdf.columns:
        candidates = [c for c in gdf.columns if c.lower() in ('alc', 'alcaldia', 'alcald')]
        if candidates:
            actual_alc = candidates[0]
            print(f"⚠️ Columna 'ALC' no encontrada; usando '{actual_alc}' en su lugar.")
        else:
            print("ERROR: No pude detectar la columna de alcaldía.", file=sys.stderr)
            sys.exit(1)
    else:
        actual_alc = COL_ALC

    # Genera límites municipales disolviendo por actual_alc
    # y obteniendo fronteras (líneas) de los polígonos
    alc_bound = gdf[[actual_alc, 'geometry']].dissolve(by=actual_alc, as_index=False)
    alc_bound['geometry'] = alc_bound.geometry.boundary
    alc_bound = gpd.GeoDataFrame(alc_bound, geometry='geometry', crs=gdf.crs)
    print(f"Alcaldías disueltas: {len(alc_bound)}")

    # Marca manzanas foco y calcula umbral Ta_max
    gdf['is_target'] = gdf[actual_alc].str.upper().isin(TARGETS)
    thr_ta = gdf[COL_TA].quantile(QT_TA)
    print(f"Umbral Ta_max P{int(100*QT_TA)} = {thr_ta:.2f}°C")

    # Itera variables
    for var in VARS:
        if var not in gdf.columns:
            print(f"⚠️ Columna '{var}' no existe; la omito.")
            continue

        label   = LABELS.get(var, var)
        thr_var = gdf[var].quantile(QT_VAR)
        print(f"\nProcesando '{var}' → umbral P{int(100*QT_VAR)} = {thr_var:.2f}%")

        # Flags alto/bajo y categoría bivariada
        gdf['high_ta']  = gdf[COL_TA] >= thr_ta
        gdf['high_var'] = gdf[var]     >= thr_var
        gdf['bivar']    = gdf.apply(
            lambda r: 'Calor↑ + Var↑' if r.high_ta and r.high_var else
                      'Calor↑ + Var↓' if r.high_ta else
                      'Var↑ + Calor↔' if r.high_var else
                      'Resto',
            axis=1
        )

        # Scatter Ta_max vs var
        plt.figure(figsize=(8,6))
        sns.scatterplot(
            x=var, y=COL_TA, data=gdf,
            hue=gdf['is_target'].map({True:'Foco', False:'Otras'}),
            palette={'Foco':'red','Otras':'lightgray'},
            alpha=0.5, s=20
        )
        plt.axhline(thr_ta, ls='--', color='k', lw=0.8,
                    label=f'P{int(100*QT_TA)} Ta={thr_ta:.1f}°C')
        plt.axvline(thr_var, ls=':', color='k', lw=0.8,
                    label=f'P{int(100*QT_VAR)} {label}={thr_var:.1f}%')
        plt.xlabel(label)
        plt.ylabel('Ta_max (°C)')
        plt.title(f'Ta_max vs {label}')
        plt.legend(frameon=False)
        plt.tight_layout()
        scatter_fn = OUT_DIR / f"scatter_{var}.png"
        plt.savefig(scatter_fn, dpi=300)
        plt.close()
        print(f"  • {scatter_fn.name}")

        # Mapa bivariado
        pal = {
            'Calor↑ + Var↑':'#d7191c',
            'Calor↑ + Var↓':'#fdae61',
            'Var↑ + Calor↔':'#2b83ba',
            'Resto':'#d3d3d3'
        }
        gdf['color'] = gdf['bivar'].map(pal)
        fig, ax = plt.subplots(1,1,figsize=(9,9))
        gdf.plot(ax=ax, color=gdf['color'], linewidth=0)
        alc_bound.plot(ax=ax, color='none', edgecolor='black', linewidth=0.5)
        cx.add_basemap(ax, crs=gdf.crs.to_string(), source=cx.providers.CartoDB.Positron,
                       alpha=0.3, zoom=12)
        ax.set_axis_off()
        for k, c in pal.items():
            ax.scatter([], [], color=c, label=k, s=50)
        ax.legend(title='Categoría', frameon=False, loc='lower left')
        plt.title(f'Hotspots Ta_max + {label}')
        plt.tight_layout()
        map_fn = OUT_DIR / f"mapa_hotspots_{var}.png"
        fig.savefig(map_fn, dpi=300)
        plt.close(fig)
        print(f"  • {map_fn.name}")

    print("\n✅ ¡Todas las figuras están en la carpeta 'figures_median_scale'!")

if __name__ == '__main__':
    main()
