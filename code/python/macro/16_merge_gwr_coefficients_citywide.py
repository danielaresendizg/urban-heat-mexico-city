# -*- coding: utf-8 -*-
"""
Une la base maestra (manzana) con todos los coeficientes GWR por alcaldía,
agregando SOLO columnas nuevas (evita duplicados), y exporta CSV + GPKG.

Requisitos: geopandas, pandas
"""

from pathlib import Path
import re
import sys
import pandas as pd
import geopandas as gpd

# ===== 1) Rutas ==============================================================
BASE = Path("/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data")
GWR_DIR = BASE / "GWR"
MASTER_GPKG = BASE / "01_Manzana" / "manzanas_IVS_20250724_con_alcaldia.gpkg"  # maestra con geometría y CVEGEO
OUT_DIR = GWR_DIR / "GWR_merge"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_OUT = OUT_DIR / "manzanas_master_con_GWR.csv"
GPKG_OUT = OUT_DIR / "manzanas_master_con_GWR.gpkg"
GPKG_LAYER = "manzanas"

# ===== 2) Lectura maestra (asegurando CVEGEO como string) ====================
try:
    gdf_master = gpd.read_file(MASTER_GPKG)
except Exception as e:
    print(f"❌ No pude leer la maestra GPKG: {MASTER_GPKG}\n{e}")
    sys.exit(1)

# Asegura CVEGEO como string para evitar pérdida de ceros
if "CVEGEO" not in gdf_master.columns:
    print("❌ La maestra no tiene columna 'CVEGEO'.")
    sys.exit(1)

gdf_master["CVEGEO"] = gdf_master["CVEGEO"].astype("string")
crs_master = gdf_master.crs
print(f"Maestra: {gdf_master.shape}  | CRS: {crs_master}")

# Lista de columnas ya presentes en la maestra
master_cols = set(gdf_master.columns)

# ===== 3) Localizar y leer todos los CSV de coeficientes =====================
csv_paths = sorted(GWR_DIR.rglob("MGWR_coeficientes_*.csv"))
print(f"CSV GWR encontrados: {len(csv_paths)}")
if not csv_paths:
    print("❌ No se encontraron CSV 'MGWR_coeficientes_*.csv'. Revisa rutas.")
    sys.exit(1)

def alcaldia_from_stem(stem: str) -> str:
    raw = re.sub(r"^MGWR_coeficientes_", "", stem)
    return raw.replace("_", " ").strip()

frames = []
for p in csv_paths:
    try:
        df = pd.read_csv(p, dtype={"CVEGEO": "string"})
    except Exception as e:
        print(f"  ⚠️ No pude leer {p.name}: {e}")
        continue

    if "CVEGEO" not in df.columns:
        print(f"  ⚠️ {p.name} no trae columna CVEGEO. Lo salto.")
        continue

    # Normaliza: elimina espacios y columnas completamente vacías
    df.columns = [c.strip() for c in df.columns]
    df = df.dropna(axis=1, how="all")

    # (Opcional) Adjunta nombre de alcaldía derivado del archivo
    df["NOM_MUN_file"] = alcaldia_from_stem(p.stem)

    frames.append(df)

if not frames:
    print("❌ No hubo CSV legibles con CVEGEO. Abortando.")
    sys.exit(1)

gwr_all = pd.concat(frames, ignore_index=True)
print(f"GWR concatenado: {gwr_all.shape}")

# ===== 4) Chequeos: duplicados de CVEGEO en CSVs =============================
dup_counts = gwr_all["CVEGEO"].value_counts()
dups = dup_counts[dup_counts > 1]
if not dups.empty:
    print("⚠️ OJO: hay CVEGEO duplicados en los CSV concatenados (muestra top 10):")
    print(dups.head(10))
    # Si NO deberían existir duplicados, descomenta para quedarte con la primera ocurrencia:
    # gwr_all = gwr_all.drop_duplicates(subset=["CVEGEO"], keep="first")

# ===== 5) Selección de columnas NUEVAS a agregar =============================
# Mantén SIEMPRE CVEGEO; de lo demás, agrega solo columnas que NO existan ya en la maestra
candidate_cols = [c for c in gwr_all.columns if c != "CVEGEO" and c not in master_cols]
if not candidate_cols:
    print("ℹ️ No hay columnas nuevas que agregar; la maestra ya contiene todas.")
    # Aún así exportamos la maestra tal cual por consistencia
    gdf_master.drop(columns=[], errors="ignore").to_file(GPKG_OUT, layer=GPKG_LAYER, driver="GPKG")
    gdf_master.drop(columns="geometry").to_csv(CSV_OUT, index=False)
    print(f"✅ CSV final: {CSV_OUT}")
    print(f"🗺️  GPKG final: {GPKG_OUT}")
    sys.exit(0)

print(f"Columnas nuevas detectadas: {len(candidate_cols)}")
# Orden sugerido: CVEGEO primero, luego nuevas
gwr_slim = gwr_all[["CVEGEO"] + candidate_cols].copy()

# ===== 6) Merge maestro + nuevas columnas (LEFT JOIN por CVEGEO) ============
# Para no duplicar columnas, el right dataframe solo contiene las nuevas
gdf_merged = gdf_master.merge(gwr_slim, on="CVEGEO", how="left", validate="one_to_one")

# ===== 7) Reporte de faltantes (manzanas sin match) ==========================
faltantes = gdf_merged[candidate_cols].isna().all(axis=1).sum()
print(f"Manzanas sin match (todas las nuevas en NaN): {faltantes}")

# ===== 8) Exportes ===========================================================
# CSV (sin geometría)
gdf_merged.drop(columns="geometry").to_csv(CSV_OUT, index=False)
print(f"✅ CSV final: {CSV_OUT}")

# GPKG (con geometría; preserva CRS)
try:
    gdf_merged = gdf_merged.set_crs(crs_master)
except Exception:
    pass
gdf_merged.to_file(GPKG_OUT, layer=GPKG_LAYER, driver="GPKG")
print(f"🗺️  GPKG final: {GPKG_OUT}")

# ===== 9) Resumen breve ======================================================
print("—" * 60)
print(f"Filas totales: {len(gdf_merged):,}")
print(f"Columnas maestra (antes): {len(master_cols)}")
print(f"Columnas nuevas agregadas: {len(candidate_cols)}")
print("Ejemplo de nuevas columnas:", candidate_cols[:10])
print("—" * 60)
