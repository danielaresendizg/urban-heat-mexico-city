import geopandas as gpd
import matplotlib.pyplot as plt
import os

# 1. Rutas a archivos
manzanas_fp = "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/manzanas_IVS_20250724.gpkg"
alcaldias_fp = "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/Boundaries/poligonos_alcaldias_cdmx/poligonos_alcaldias_cdmx.shp"

output_dir = "output_maps_cdmx"
os.makedirs(output_dir, exist_ok=True)

manzanas = gpd.read_file(manzanas_fp)
alcaldias = gpd.read_file(alcaldias_fp)
manzanas = manzanas.to_crs(epsg=3857)
alcaldias = alcaldias.to_crs(epsg=3857)

# Un solo polígono para recortar todo (CDMX boundary)
cdmx_shape = alcaldias.unary_union

variables = {
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

for grupo, vars in variables.items():
    for var in vars:
        if var not in manzanas.columns:
            print(f"[ADVERTENCIA] Variable {var} no encontrada en el GPKG.")
            continue
        # CLIP al polígono de CDMX: solo manzanas dentro de la ciudad
        data = manzanas[manzanas.geometry.within(cdmx_shape)].copy()
        fig, ax = plt.subplots(figsize=(9, 9))
        plot = data.plot(
            column=var,
            ax=ax,
            cmap="YlOrRd",
            legend=False,
            vmin=0, vmax=100,
            linewidth=0,
            alpha=1
        )
        alcaldias.boundary.plot(ax=ax, color="k", linewidth=1)
        ax.set_axis_off()
        ax.set_title(
            f"CDMX – {grupo.capitalize()} – {var.replace('_',' ').capitalize()} (%)",
            fontsize=16, fontweight='bold', pad=12
        )
        # --- Barra de color más corta y minimalista ---
        sm = plt.cm.ScalarMappable(cmap="YlOrRd", norm=plt.Normalize(vmin=0, vmax=100))
        cbar = fig.colorbar(sm, ax=ax, fraction=0.030, pad=0.03)
        cbar.set_label(f"{var.replace('_',' ').capitalize()} (%)", fontsize=12)
        cbar.ax.tick_params(labelsize=11)
        plt.tight_layout()
        output_path = os.path.join(output_dir, f"cdmx_{grupo}_{var}_pct_minimal.png")
        plt.savefig(output_path, dpi=300, bbox_inches="tight", transparent=True)
        plt.close()
        print(f"[OK] Guardado: {output_path}")
