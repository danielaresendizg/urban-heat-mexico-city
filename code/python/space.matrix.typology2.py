# -*- coding: utf-8 -*-
"""
Clasificación tipológica Spacematrix (nivel MANZANA) – v2 con QA
===============================================================

Cambios clave respecto a tu script original:
- **Nueva categoría '0P – 0 propiedad (sin catastro asignado)'** para casos
  con **FSI == 0 & GSI > 0 & n_props == 0** (o nulo→0). Antes quedaban como
  "Mixto/indeterminado"; ahora se separan como **Data Quality** explícito.
- **Reclasificación de 'Mixto/indeterminado' por tolerancias** (MIXTO_limite):
  si una manzana no cae en rangos exactos pero está cerca de los límites
  (±eps en GSI/FSI y ±eps_L en L), se "encaja" en la tipología más probable
  respetando el **PRIORITY_ORDER**.
- **Auditoría automática** al final: imprime y guarda un resumen con
  conteos/porcentajes que **confirman los criterios aplicados** (número de
  '0P', número de 'Mixto' re-clasificados por tolerancia, etc.).

Entrada
-------
- GPKG y layer con columnas: FSI (float), GSI (float), L_equiv (opcional),
  OSR (opcional), **n_props** (int; # de predios enlazados por manzana).
  Si L_equiv falta, se calcula como FSI/GSI cuando GSI>0.

Salida
------
- Nuevo layer con: `typology_code_base`, `typology_code_final`,
  `typology_sm_final`, banderas `flag_mixto_dq`, `flag_mixto_limite` y
  columnas de diagnóstico. También CSV espejo y un .md con el resumen.

Parámetros de tolerancia
------------------------
- `EPS_G=0.02`, `EPS_F=0.10`, `EPS_L=0.5` (ajustables).

"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from pyogrio import list_layers

# ========================== CONFIGURACIÓN ====================================
GPKG = Path("/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/manzanas_thermal_GWR_spacematrix_hotspots_final.gpkg")
LAYER_IN   = "manzanas_thermal_GWR_spacematrix_hotspots_final"
LAYER_OUT  = "manzanas_typology_SM_v2"   # nuevo layer de salida
NOTE_MD    = GPKG.with_name(GPKG.stem + "_Spacematrix_Tipologias_v2.md")
SUMMARY_CSV= GPKG.with_name(GPKG.stem + "_SMv2_resumen.csv")

# Tolerancias para MIXTO_limite
EPS_G = 0.02  # GSI ±0.02
EPS_F = 0.10  # FSI ±0.10
EPS_L = 0.50  # L  ±0.5

# =========================== CATÁLOGO ========================================
CATALOG = {
    "00": ("Sin datos", "FSI/GSI faltantes o GSI ≤ 0."),
    "01": ("Pabellón abierto", "Edificios aislados con mucha área libre; baja altura (1–3 pisos)."),
    "02": ("Fila / Adosada baja", "Casas en hilera/adosadas; baja altura; pequeñas áreas libres."),
    "03": ("Perímetro bajo", "Manzana cerrada con patio interior; altura baja (1–3)."),
    "04": ("Perímetro medio", "Perímetro más alto/denso; 3–6 pisos."),
    "05": ("Perímetro denso", "Cobertura muy alta; altura media; calles/patios estrechos."),
    "06": ("Barras", "Bloques lineales separados; 4–8 pisos; áreas abiertas entre ellos."),
    "07": ("Torre en parque", "Torres altas en entorno abierto; 6–12 pisos; mucha ventilación."),
    "08": ("Supercompacta alta", "Basamento + torres; compacidad y densidad muy altas; 6–12 pisos."),
    "09": ("Continuo compacto bajo", "Cobertura casi total pero 1–2 pisos; calles muy cerradas."),
    "10": ("Mixto / indeterminado", "Mezcla o fuera de los rangos anteriores."),
    # Nueva categoría de QA (código alfanumérico para distinguirla del 00):
    "0P": ("0 propiedad (sin catastro)", "GSI>0, FSI=0 y n_props=0 → sin predios asociados a la manzana."),
}

# Cada entrada: (GSI_min, GSI_max, FSI_min, FSI_max, L_min, L_max)
RANGES = {
    "01": (0.10, 0.30, 0.2, 1.0, 1.0, 3.0),
    "02": (0.30, 0.50, 0.5, 1.5, 1.0, 3.0),
    "03": (0.50, 0.70, 0.8, 2.0, 1.0, 3.0),
    "04": (0.50, 0.70, 1.5, 4.0, 3.0, 6.0),
    "05": (0.70, 0.90, 2.0, 5.0, 3.0, 6.0),
    "06": (0.30, 0.55, 1.5, 3.5, 4.0, 8.0),
    "07": (0.15, 0.35, 2.5, 6.0, 6.0, 12.0),
    "08": (0.60, 0.90, 4.0, 8.0, 6.0, 12.0),
    "09": (0.70, 0.90, 0.8, 1.5, 1.0, 2.0),
}

# Orden de prioridad para resolver solapes (primero extremos)
PRIORITY_ORDER = ["08", "07", "06", "05", "04", "03", "09", "02", "01"]

# ========================== HELPERS ==========================================
def _in_range(x, lo, hi):
    if pd.isna(x):
        return False
    return (x >= lo) and (x <= hi)

def _match(code, FSI, GSI, L):
    g_lo, g_hi, f_lo, f_hi, l_lo, l_hi = RANGES[code]
    return (_in_range(GSI, g_lo, g_hi) and _in_range(FSI, f_lo, f_hi) and _in_range(L, l_lo, l_hi))

def _match_expanded(code, FSI, GSI, L, eps_g=EPS_G, eps_f=EPS_F, eps_l=EPS_L):
    g_lo, g_hi, f_lo, f_hi, l_lo, l_hi = RANGES[code]
    return (
        _in_range(GSI, g_lo - eps_g, g_hi + eps_g) and
        _in_range(FSI, f_lo - eps_f, f_hi + eps_f) and
        _in_range(L,   l_lo - eps_l, l_hi + eps_l)
    )

def classify_exact(FSI, GSI, L_equiv):
    """Clasificación estricta con rangos originales."""
    if pd.isna(FSI) or pd.isna(GSI) or (GSI <= 0):
        return "00"
    L = L_equiv if not pd.isna(L_equiv) else (FSI / GSI if GSI > 0 else np.nan)
    for code in PRIORITY_ORDER:
        if _match(code, FSI, GSI, L):
            return code
    return "10"  # mixto/indeterminado

def classify_with_tolerance(FSI, GSI, L_equiv):
    """Si no encaja exacto, intenta con rangos expandidos (MIXTO_limite)."""
    base = classify_exact(FSI, GSI, L_equiv)
    if base != "10":
        return base, False  # no fue necesario expandir
    if pd.isna(FSI) or pd.isna(GSI) or (GSI <= 0):
        return "00", False
    L = L_equiv if not pd.isna(L_equiv) else (FSI / GSI if GSI > 0 else np.nan)
    for code in PRIORITY_ORDER:
        if _match_expanded(code, FSI, GSI, L):
            return code, True  # re-clasificado por tolerancia
    return "10", False

# ========================== LECTURA ==========================================
print("Capas disponibles:", list_layers(GPKG))

gdf = gpd.read_file(GPKG, layer=LAYER_IN, engine="pyogrio")

# Normalizar tipos
for col in ["FSI", "GSI", "L_equiv", "OSR", "n_props"]:
    if col in gdf.columns:
        gdf[col] = pd.to_numeric(gdf[col], errors="coerce")

# L_equiv si falta
if "L_equiv" not in gdf.columns:
    gdf["L_equiv"] = np.where((gdf["GSI"] > 0) & (~gdf["FSI"].isna()), gdf["FSI"] / gdf["GSI"], np.nan)

# ======================== CLASIFICACIÓN BASE =================================
print("Clasificando (rangos exactos)…", flush=True)

gdf["typology_code_base"] = [
    classify_exact(F, G, L) for F, G, L in gdf[["FSI", "GSI", "L_equiv"]].itertuples(index=False, name=None)
]
gdf["typology_name_base"] = [CATALOG.get(c, ("Desconocida", ""))[0] for c in gdf["typology_code_base"]]

# ================== FLAGS: MIXTO_DQ y MIXTO_limite ===========================
# MIXTO_DQ: FSI=0 & GSI>0 & n_props=0  → código '0P'
print("Marcando MIXTO_DQ (FSI=0 & GSI>0 & n_props=0)…", flush=True)

n_props_series = gdf["n_props"] if "n_props" in gdf.columns else pd.Series(np.nan, index=gdf.index)
flag_mixto_dq = (
    (gdf["typology_code_base"] == "10") &
    (gdf["FSI"].fillna(0) == 0) &
    (gdf["GSI"].fillna(0) > 0) &
    (n_props_series.fillna(0).astype(float) == 0)
)

gdf["flag_mixto_dq"] = flag_mixto_dq.astype(int)

# MIXTO_limite: base=10 pero cae en rangos con tolerancia → se re-clasifica
print("Reclasificando MIXTO_limite (tolerancias)…", flush=True)

reclass_codes = []
reclass_flags = []
for F, G, L, base in gdf[["FSI","GSI","L_equiv","typology_code_base"]].itertuples(index=False, name=None):
    if base != "10":
        reclass_codes.append(base)
        reclass_flags.append(0)
        continue
    code2, used_tol = classify_with_tolerance(F, G, L)
    reclass_codes.append(code2)
    reclass_flags.append(1 if (used_tol and code2 != "10") else 0)

# Si ya es MIXTO_DQ, prevalece '0P' por encima de re-clasificación por tolerancia
reclass_codes = pd.Series(reclass_codes, index=gdf.index)
reclass_codes.loc[flag_mixto_dq] = "0P"

gdf["typology_code_final"] = reclass_codes

# Nombre final
gdf["typology_sm_final"] = [CATALOG.get(c, ("Desconocida",""))[0] for c in gdf["typology_code_final"]]

# Flag explícito de MIXTO_limite aplicado
gdf["flag_mixto_limite"] = (pd.Series(reclass_flags, index=gdf.index).astype(int))
# Pero si terminó como '0P', no es "limite" sino DQ → set 0
gdf.loc[gdf["typology_code_final"]=="0P", "flag_mixto_limite"] = 0

# Diagnóstico básico
gdf["diag_reason"] = ""
gdf.loc[gdf["typology_code_final"]=="0P", "diag_reason"] = "FSI=0 & GSI>0 & n_props=0"
gdf.loc[(gdf["typology_code_base"]=="10") & (gdf["typology_code_final"]!="0P") & (gdf["typology_code_final"]!="10"), "diag_reason"] = "Reclasificada por tolerancia"

# ======================== RESUMEN / QA =======================================
print("Generando resumen de QA…", flush=True)

def _count(s, val):
    return int((s==val).sum())

total = int(gdf.shape[0])
base_mixto = _count(gdf["typology_code_base"], "10")
final_mixto = _count(gdf["typology_code_final"], "10")
zeroP = _count(gdf["typology_code_final"], "0P")
reclass_tol = int(((gdf["typology_code_base"]=="10") & (gdf["typology_code_final"]!="10") & (gdf["typology_code_final"]!="0P")).sum())

summary = pd.DataFrame({
    "metric": [
        "total_rows",
        "mixto_base_n",
        "mixto_final_n",
        "0P_n (FSI=0 & GSI>0 & n_props=0)",
        "reclasificados_por_tolerancia_n"
    ],
    "value": [total, base_mixto, final_mixto, zeroP, reclass_tol]
})

# Guardar resumen y parámetros
summary.to_csv(SUMMARY_CSV, index=False)

params = {
    "ranges": RANGES,
    "priority": PRIORITY_ORDER,
    "tolerancias": {"EPS_G":EPS_G, "EPS_F":EPS_F, "EPS_L":EPS_L},
    "catalogo": {k:v[0] for k,v in CATALOG.items()},
}

# ======================== SALIDA =============================================
print(f"→ Escribiendo layer '{LAYER_OUT}' en {GPKG.name}")
# Evitar perder columnas originales; dejamos nuevas columnas añadidas
out_cols = list(gdf.columns)

gdf.to_file(GPKG, layer=LAYER_OUT, driver="GPKG", engine="pyogrio")

csv_out = GPKG.with_suffix(".csv")
print(f"→ Espejo CSV: {csv_out}")
(gdf.drop(columns="geometry", errors="ignore")
    .to_csv(csv_out, index=False, encoding="utf-8"))

# Nota/Markdown con parámetros y resumen
lines = []
lines.append("# Spacematrix Tipologías – v2 (con QA)\n\n")
lines.append("## Resumen de parámetros\n")
lines.append(f"- PRIORITY_ORDER: {PRIORITY_ORDER}\n")
lines.append(f"- Tolerancias: EPS_G={EPS_G}, EPS_F={EPS_F}, EPS_L={EPS_L}\n\n")
lines.append("## Catálogo\n")
for k,(nm,ds) in CATALOG.items():
    lines.append(f"- **{k}**: {nm} – {ds}\n")
lines.append("\n## Resumen QA (confirmación de criterios)\n")
lines.append(summary.to_csv(index=False))
lines.append("\n\n**Criterios confirmados:**\n- '0P' sólo se asigna cuando **FSI=0 & GSI>0 & n_props=0**.\n- 'Mixto' re-clasificado por tolerancia únicamente cuando cae en rangos expandidos ±(EPS_G, EPS_F, EPS_L).\n")

NOTE_MD.write_text("".join(lines), encoding="utf-8")

print("Listo ✅  (SM v2 con 0P y tolerancias, resumen exportado)")
