#!/usr/bin/env python3
"""
generate_ivs_final.py

Genera indicadores clave de vulnerabilidad por manzana en CDMX
y los exporta junto con variables térmicas, solo con las columnas requeridas.
"""

from pathlib import Path
import datetime as dt
import argparse
import pandas as pd
import geopandas as gpd
import numpy as np

# ---------------------------- ARGUMENTOS -----------------------------------
parser = argparse.ArgumentParser(description="Genera IVS de manzanas CDMX (indicadores clave)")
parser.add_argument(
    "--base",
    default=str(Path.home() / "Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana"),
    help="Carpeta base de datos"
)
parser.add_argument(
    "--date",
    default=dt.date.today().strftime("%Y%m%d"),
    help="Sufijo de fecha para versionar archivos"
)
args = parser.parse_args()
base = Path(args.base)
date = args.date

# ---------------------------- RUTAS ----------------------------------------
csv_path = base / "ageb_mza_urbana_09_cpv2020/conjunto_de_datos/conjunto_de_datos_ageb_urbana_09_cpv2020.csv"
shp_path = base / "poligono_manzanas_cdmx (1)/poligono_manzanas_cdmx.shp"
out_gpkg = base / f"manzanas_IVS_{date}.gpkg"
out_csv  = base / f"manzanas_IVS_{date}.csv"

# ---------------------- LECTURA Y LIMPIEZA DE DATOS -------------------------
print(f"Abriendo: {csv_path}")
print("¿Existe el archivo?", csv_path.exists())
if not csv_path.exists():
    raise FileNotFoundError(f"El archivo no existe: {csv_path}")

df = pd.read_csv(csv_path)
df.columns = df.columns.str.strip()  # Limpia espacios en nombres de columna

if 'CVEGEO' not in df.columns:
    for col, w in [("ENTIDAD",2),("MUN",3),("LOC",4),("AGEB",4),("MZA",3)]:
        df[col] = df[col].astype(str).str.zfill(w)
    df['CVEGEO'] = df['ENTIDAD'] + df['MUN'] + df['LOC'] + df['AGEB'] + df['MZA']

# --- Lista de variables que debes convertir a numérico (ajústala según tus columnas reales)
vars_needed = [
    "POBTOT", "P_0A2", "P_3A5", "P_6A11", "P_8A14", "P_15YMAS", "POB65_MAS", "POB0_14",
    "P_3YMAS", "P3YM_HLI", "POB_AFRO", "PCON_DISC",
    "P15YM_SE", "P15PRI_CO", "P15SEC_CO", "P_18YMAS", "P18YM_PB",
    "P_12YMAS", "POCUPADA", "PDESOCUP", "PE_INAC",
    "PDER_SS", "PSINDER", "VPH_NDACMM", "PROM_OCUP", "POBFEM", "POBMAS", "OCUPVIVPAR", "TVIVHAB"
]
for v in vars_needed:
    if v in df.columns:
        df[v] = pd.to_numeric(df[v], errors='coerce')

# ---------------------- VARIABLES AUXILIARES --------------------------------
def add_prom_ocup(df):
    if "TVIVHAB" in df.columns and "OCUPVIVPAR" in df.columns:
        df["PROM_OCUP"] = np.where(df["TVIVHAB"] == 0, 0, df["OCUPVIVPAR"] / df["TVIVHAB"])
    return df

def add_P_15A64(df):
    if "P_15YMAS" in df.columns and "POB65_MAS" in df.columns:
        df["P_15A64"] = df["P_15YMAS"] - df["POB65_MAS"]
    return df

df = add_prom_ocup(df)
df = add_P_15A64(df)

# ---------------------- INDICADORES -----------------------------------------
prop_vars = [
    # Age
    ("pct_0a5",         lambda df: np.where(df["POBTOT"] == 0, 0, (df["P_0A2"] + df["P_3A5"]) / df["POBTOT"] * 100)),
    ("pct_6a14",        lambda df: np.where(df["POBTOT"] == 0, 0, (df["P_6A11"] + df["P_8A14"]) / df["POBTOT"] * 100)),
    ("pct_15a64",       lambda df: np.where(df["POBTOT"] == 0, 0, df["P_15A64"] / df["POBTOT"] * 100)),
    ("pct_65plus",      lambda df: np.where(df["POBTOT"] == 0, 0, df["POB65_MAS"] / df["POBTOT"] * 100)),

    # Ethnic
    ("pct_ethnic_afro", lambda df: np.where(df["POBTOT"] == 0, 0, df["POB_AFRO"] / df["POBTOT"] * 100)),
    ("pct_ethnic_ind",  lambda df: np.where(df["POBTOT"] == 0, 0, df["P3YM_HLI"] / df["POBTOT"] * 100)),
    ("pct_ethnic_other",lambda df: np.where(df["POBTOT"] == 0, 0, (df["POBTOT"] - (df["POB_AFRO"] + df["P3YM_HLI"])) / df["POBTOT"] * 100)),

    # Disability
    ("pct_without_disc",lambda df: np.where(df["POBTOT"] == 0, 0, (df["POBTOT"] - df["PCON_DISC"]) / df["POBTOT"] * 100)),
    ("pct_with_disc",   lambda df: np.where(df["POBTOT"] == 0, 0, df["PCON_DISC"] / df["POBTOT"] * 100)),

    # Education (15+)
    ("pct_no_school",       lambda df: np.where(df["P_15YMAS"] == 0, 0, df["P15YM_SE"] / df["P_15YMAS"] * 100)),
    ("pct_elementary_edu",  lambda df: np.where(df["P_15YMAS"] == 0, 0, df["P15PRI_CO"] / df["P_15YMAS"] * 100)),
    ("pct_elementary2_edu", lambda df: np.where(df["P_15YMAS"] == 0, 0, df["P15SEC_CO"] / df["P_15YMAS"] * 100)),
    ("pct_more_edu",        lambda df: np.where(df["P_18YMAS"] == 0, 0, df["P18YM_PB"] / df["P_18YMAS"] * 100)),

    # Economy (12+)
    ("pct_ocup",       lambda df: np.where(df["P_12YMAS"] == 0, 0, df["POCUPADA"] / df["P_12YMAS"] * 100)),
    ("pct_desocup",    lambda df: np.where(df["P_12YMAS"] == 0, 0, df["PDESOCUP"] / df["P_12YMAS"] * 100)),
    ("pct_inac",       lambda df: np.where(df["P_12YMAS"] == 0, 0, df["PE_INAC"] / df["P_12YMAS"] * 100)),

    # Health
    ("pct_serv_med",   lambda df: np.where(df["POBTOT"] == 0, 0, df["PDER_SS"] / df["POBTOT"] * 100)),
    ("pct_no_serv_med",lambda df: np.where(df["POBTOT"] == 0, 0, df["PSINDER"] / df["POBTOT"] * 100)),

    # Mobility
    ("pct_pop_sin_auto",   lambda df: np.where(df["POBTOT"] == 0, 0, (df["VPH_NDACMM"] * df["PROM_OCUP"]) / df["POBTOT"] * 100)), # CORREGIDO

    # Care/Dependency
    ("rel_dependencia_0_14", lambda df: np.where((df["P_15A64"] - df["POB65_MAS"]) == 0, 0, df["POB0_14"] / (df["P_15A64"] - df["POB65_MAS"]) * 100)),

    # Gender
    ("rel_h_m",        lambda df: np.where(df["POBFEM"] == 0, 0, df["POBMAS"] / df["POBFEM"] * 100)),
]

# Calcular proporciones finales
for name, func in prop_vars:
    df[name] = func(df)

df["pct_pop_auto"] = 100 - df["pct_pop_sin_auto"]

# ----------- INCORPORAR VARIABLES TÉRMICAS Y AMBIENTALES POR MANZANA -------
thermal_gpkg = base / "manzana_thermal-IVS.gpkg"
thermal_vars = [
    'Ta_mean', 'Ta_max', 'Albedo_mean', 'LST_mean',
    'NDBI_mean', 'NDVI_mean', 'UHI_mean', 'UHI_max'
]
if thermal_gpkg.exists():
    gdf_thermal = gpd.read_file(thermal_gpkg)
    cols_to_merge = ['CVEGEO'] + [col for col in thermal_vars if col in gdf_thermal.columns]
    df = df.merge(gdf_thermal[cols_to_merge], on='CVEGEO', how='left')

# -------------------- DEFINIR COLUMNAS FINALES -----------------------------
final_cols = ['CVEGEO'] + [c for c, _ in prop_vars] + ['pct_pop_auto']
final_cols += [col for col in thermal_vars if col in df.columns]

# ------------------ JOIN ESPACIAL CON MANZANAS Y EXPORT -------------------
gdf = gpd.read_file(shp_path)
if 'CVEGEO' not in gdf.columns:
    for col, w in [("CVE_ENT",2),("CVE_MUN",3),("CVE_LOC",4),("CVE_AGEB",4),("CVE_MZA",3)]:
        gdf[col] = gdf[col].astype(str).str.zfill(w)
    gdf['CVEGEO'] = gdf['CVE_ENT'] + gdf['CVE_MUN'] + gdf['CVE_LOC'] + gdf['CVE_AGEB'] + gdf['CVE_MZA']

merged = gdf.set_index('CVEGEO').join(df.set_index('CVEGEO'), how='inner')
auto = merged.reset_index()

# -------------------- LIMPIEZA: LLENA NaN CON 0 ---------------------------
auto[final_cols] = auto[final_cols].fillna(0)

# -------------- VERIFICACIÓN ANTES DE EXPORTAR --------------
faltantes = [col for col in final_cols if col not in auto.columns]
if faltantes:
    print("⚠️  FALTAN COLUMNAS en el DataFrame:", faltantes)
    raise Exception("Corrige los nombres/cálculos, falta alguna variable.")

# Solo las columnas finales + geometría
gdf_out = auto[final_cols + ['geometry']]
gdf_out.to_file(str(out_gpkg), layer='manzanas', driver='GPKG')
auto[final_cols].to_csv(str(out_csv), index=False)

print(f"✅ GeoPackage y CSV exportados en: {out_gpkg} y {out_csv}")
