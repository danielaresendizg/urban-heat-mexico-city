# -*- coding: utf-8 -*-
"""
Clasificación tipológica Spacematrix (a nivel MANZANA) para CDMX
Versión: criterios adaptados al diagrama FSI–GSI del libro *Spacematrix* (Berghauser Pont & Haupt, 2020),
con descripciones simplificadas para fácil lectura en la tesis.

NOTA (tabla de referencia usada en la clasificación)
---------------------------------------------------
Código | Nombre                  | Descripción sencilla
------ | ----------------------- | --------------------------------------------------------------
01     | Pabellón abierto        | Edificios aislados con mucha área libre; baja altura (1–3 pisos).
02     | Fila / Adosada baja     | Casas en hilera/adosadas; baja altura; pequeñas áreas libres.
03     | Perímetro bajo          | Manzana cerrada con patio interior; altura baja (1–3).
04     | Perímetro medio         | Perímetro más alto/denso; 3–6 pisos.
05     | Perímetro denso         | Cobertura muy alta; altura media; calles/patios estrechos.
06     | Barras                  | Bloques lineales separados; 4–8 pisos; áreas abiertas entre ellos.
07     | Torre en parque         | Torres altas en entorno abierto; 6–12 pisos; mucha ventilación.
08     | Supercompacta alta      | Basamento + torres; compacidad y densidad muy altas; 6–12 pisos.
09     | Continuo compacto bajo  | Cobertura casi total pero 1–2 pisos; calles muy cerradas.
10     | Mixto / indeterminado   | Mezcla o fuera de los rangos anteriores.

Rangos típicos (para la asignación, con líneas de altura equivalente L = FSI / GSI):
  - 01 Pabellón abierto:        GSI 0.10–0.30, FSI 0.2–1.0,  L 1–3
  - 02 Fila/Adosada baja:       GSI 0.30–0.50, FSI 0.5–1.5,  L 1–3
  - 03 Perímetro bajo:          GSI 0.50–0.70, FSI 0.8–2.0,  L 1–3
  - 04 Perímetro medio:         GSI 0.50–0.70, FSI 1.5–4.0,  L 3–6
  - 05 Perímetro denso:         GSI 0.70–0.90, FSI 2.0–5.0,  L 3–6
  - 06 Barras:                  GSI 0.30–0.55, FSI 1.5–3.5,  L 4–8
  - 07 Torre en parque:         GSI 0.15–0.35, FSI 2.5–6.0,  L 6–12
  - 08 Supercompacta alta:      GSI 0.60–0.90, FSI 4.0–8.0,  L 6–12
  - 09 Continuo compacto bajo:  GSI 0.70–0.90, FSI 0.8–1.5,  L 1–2
  - 10 Mixto/indeterminado:     resto

Importante:
- Estos rangos son “zonas tipológicas” del diagrama FSI–GSI; hay solapes. Resolvemos con un orden
  de prioridad que favorece primero “extremos” (08/07/06/05/04/03/09/02/01). Si prefieres otra
  prioridad, ajusta la lista PRIORITY_ORDER.
- OSR no se usa explícitamente en la asignación (igual que en el libro), pero queda en la tabla por si
  quieres análisis complementarios.

Requisitos de columnas en el layer de entrada:
- FSI (float), GSI (float); opcional L_equiv (si no existe se calcula como FSI/GSI cuando GSI>0), OSR (float opcional).
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
from pyogrio import list_layers  # más rápido/liviano que fiona

# === Rutas (ajusta si tu layer/archivo se llama distinto) ======================
GPKG = Path("/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/manzanas_thermal_GWR_spacematrix_hotspots_final.gpkg")
LAYER_IN  = "manzanas_thermal_GWR_spacematrix_hotspots_final"
LAYER_OUT = "manzanas_tipologia_SM"  # NUEVO layer
NOTE_MD   = GPKG.with_name(GPKG.stem + "_Spacematrix_Tipologias.md")

print("Capas disponibles:", list_layers(GPKG))

# === Catálogo (código -> nombre y descripción sencilla) =======================
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
}

# === Rangos operativos (Spacematrix) ==========================================
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

# Orden de prioridad para resolver solapes (primero se intenta 08, luego 07, etc.)
PRIORITY_ORDER = ["08", "07", "06", "05", "04", "03", "09", "02", "01"]

def _in_range(x, lo, hi):
    """Incluye extremos; tolera NaN regresando False."""
    if pd.isna(x):
        return False
    return (x >= lo) and (x <= hi)

def _match(code, FSI, GSI, L):
    g_lo, g_hi, f_lo, f_hi, l_lo, l_hi = RANGES[code]
    return (_in_range(GSI, g_lo, g_hi) and
            _in_range(FSI, f_lo, f_hi) and
            _in_range(L,   l_lo, l_hi))

def classify_spacematrix(FSI, GSI, L_equiv):
    # Guardas
    if pd.isna(FSI) or pd.isna(GSI) or (GSI <= 0):
        return "00"

    # Si no hay L, calcúlala (sólo si GSI>0)
    L = L_equiv
    if pd.isna(L) and (GSI > 0):
        L = FSI / GSI

    # Recorre en orden de prioridad para resolver solapes
    for code in PRIORITY_ORDER:
        if _match(code, FSI, GSI, L):
            return code

    # Si nada coincide, mixto/indeterminado
    return "10"

# === Leer layer y normalizar columnas =========================================
gdf = gpd.read_file(GPKG, layer=LAYER_IN, engine="pyogrio")
for col in ["FSI", "GSI"]:
    if col not in gdf.columns:
        raise ValueError(f"Falta la columna '{col}' en la capa '{LAYER_IN}'.")
    gdf[col] = pd.to_numeric(gdf[col], errors="coerce")

# L_equiv si no existe
if "L_equiv" in gdf.columns:
    gdf["L_equiv"] = pd.to_numeric(gdf["L_equiv"], errors="coerce")
else:
    gdf["L_equiv"] = np.where((gdf["GSI"] > 0) & (~gdf["FSI"].isna()),
                              gdf["FSI"] / gdf["GSI"], np.nan)

# OSR es opcional; lo mantenemos si existe
if "OSR" in gdf.columns:
    gdf["OSR"] = pd.to_numeric(gdf["OSR"], errors="coerce")

# === Clasificar ===============================================================
codes = []
for FSI, GSI, L in gdf[["FSI", "GSI", "L_equiv"]].itertuples(index=False, name=None):
    codes.append(classify_spacematrix(FSI, GSI, L))

gdf["typology_code"] = codes
gdf["typology_sm"]   = [CATALOG[c][0] for c in codes]
gdf["typology_desc"] = [CATALOG[c][1] for c in codes]

# Auditoría mínima: guardar los parámetros de rangos y prioridad
gdf.attrs["spacematrix_params"] = {
    "ranges": RANGES,
    "priority": PRIORITY_ORDER
}

# === Guardar nuevo layer en el mismo GPKG ====================================
gdf.to_file(GPKG, layer=LAYER_OUT, driver="GPKG", engine="pyogrio")
print(f"OK: creado layer '{LAYER_OUT}' en {GPKG.name}")

# === Export espejo CSV (sin geometría) =======================================
csv_out = GPKG.with_suffix(".csv")
gdf.drop(columns="geometry").to_csv(csv_out, index=False, encoding="utf-8")
print(f"CSV espejo: {csv_out}")

# === Exportar la nota/tablas a un .md anexo para la tesis =====================
note = []
note.append("# Tipologías Spacematrix – versión simplificada\n")
note.append("| Código | Nombre | Descripción | GSI | FSI | L (pisos) |\n")
note.append("|---|---|---|---|---|---|\n")
TABLE = {
    "01": ("Pabellón abierto",       "Edificios aislados; mucha área libre; 1–3 pisos.",     "0.10–0.30", "0.2–1.0",  "1–3"),
    "02": ("Fila / Adosada baja",    "Hilera/adosada; baja altura; áreas libres pequeñas.",  "0.30–0.50", "0.5–1.5",  "1–3"),
    "03": ("Perímetro bajo",         "Perímetro con patio; altura baja.",                    "0.50–0.70", "0.8–2.0",  "1–3"),
    "04": ("Perímetro medio",        "Perímetro más alto/denso.",                            "0.50–0.70", "1.5–4.0",  "3–6"),
    "05": ("Perímetro denso",        "Cobertura muy alta; altura media.",                    "0.70–0.90", "2.0–5.0",  "3–6"),
    "06": ("Barras",                 "Bloques lineales separados; 4–8 pisos.",               "0.30–0.55", "1.5–3.5",  "4–8"),
    "07": ("Torre en parque",        "Torres altas en entorno abierto.",                     "0.15–0.35", "2.5–6.0",  "6–12"),
    "08": ("Supercompacta alta",     "Basamento + torres; muy denso.",                       "0.60–0.90", "4.0–8.0",  "6–12"),
    "09": ("Continuo compacto bajo", "Cobertura casi total; 1–2 pisos.",                     "0.70–0.90", "0.8–1.5",  "1–2"),
    "10": ("Mixto / indeterminado",  "Mezcla o fuera de rangos.",                            "—",         "—",        "—"),
}
for k in ["01","02","03","04","05","06","07","08","09","10"]:
    nm, ds, g, f, l = TABLE[k]
    note.append(f"| {k} | {nm} | {ds} | {g} | {f} | {l} |\n")

note.append("\n**Observaciones**:\n")
note.append("- Asignación basada en zonas FSI–GSI del diagrama *Spacematrix*; L (=FSI/GSI) se usa como comprobación.\n")
note.append("- Los rangos pueden solaparse; la resolución de conflictos sigue la prioridad: " + " > ".join(PRIORITY_ORDER) + ".\n")
note.append("- OSR no interviene en la clasificación (igual que en el libro), pero puede analizarse a posteriori.\n")

NOTE_MD.write_text("".join(note), encoding="utf-8")
print(f"Nota de tipologías exportada a: {NOTE_MD}")
