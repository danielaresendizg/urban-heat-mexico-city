import pandas as pd
import geopandas as gpd
from pathlib import Path
import numpy as np

# ─── Definir rutas ─────────────────────────────────────────────────────
BASE     = Path("/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/Data/RedMet")
CSV_EST  = BASE / "estaciones_operacion_CDMX.csv"
GPKG_EST = BASE / "estaciones_operacion_CDMX.gpkg"
HIST_DIR = BASE / "Estaciones_historico_14-24"
OUT_DIR  = BASE / "procesados"

# ─── Cargar estaciones ──────────────────────────────────────────────────
est_df = pd.read_csv(CSV_EST)
gdf_est = gpd.read_file(GPKG_EST)

print(f"Carga CSV: {len(est_df)} filas desde {CSV_EST.name}")
print(est_df.head(3))
print(f"Carga GPKG: {len(gdf_est)} geometrías desde {GPKG_EST.name}")
print(gdf_est.head(3))

# ─── Función para convertir .xls ancho a DataFrame largo ────────────────
def melt_xls(path_xls: Path, varname: str, year: int) -> pd.DataFrame:
    engine = 'xlrd' if path_xls.suffix.lower() == '.xls' else 'openpyxl'
    df = pd.read_excel(path_xls, engine=engine)
    long_df = df.melt(
        id_vars=['FECHA','HORA'],
        var_name='estacion_id',
        value_name=varname
    ).dropna(subset=[varname])
    long_df = long_df[long_df.estacion_id.isin(est_df['cve_estac'])]
    long_df['datetime'] = long_df['FECHA'] + pd.to_timedelta(long_df['HORA'], unit='h')
    long_df['year']     = year
    return long_df[['estacion_id','datetime',varname,'year']]

# ─── Prueba de melt_xls para 2014TMP.xls en 14REDMET ────────────────
test_path = HIST_DIR / "14REDMET" / "2014TMP.xls"
df_test   = melt_xls(test_path, "Ta", 2014)
print("Prueba melt_xls:", df_test.shape)
print(df_test.head(5))

# ─── Procesar todos los años 2014–2024 para Ta y RH ────────────────────
YEARS   = range(2014, 2025)
records = []

for yr in YEARS:
    sub    = HIST_DIR / f"{str(yr)[-2:]}REDMET"
    df_t   = melt_xls(sub / f"{yr}TMP.xls", "Ta", yr)
    df_h   = melt_xls(sub / f"{yr}RH.xls",  "RH", yr)
    records.append(df_t.merge(df_h, on=["estacion_id","datetime","year"]))

# ─── Concatenar y limpiar antes de filtrar ─────────────────────────────
df_all = pd.concat(records, ignore_index=True)

# 1) Eliminar códigos de error –99 y variantes
df_all[['Ta','RH']] = df_all[['Ta','RH']].replace([-99, -99.0, -999], pd.NA)
df_all = df_all.dropna(subset=['Ta','RH'])

# 2) Filtrar solo verano (jun-ago)
df_all['mes']    = df_all.datetime.dt.month
df_summer        = df_all[df_all.mes.isin([6,7,8])].drop(columns='mes')

# ─── DEBUG: verificar rango de fechas ───────────────────────────────────
print("Rango fechas df_summer:", df_summer.datetime.min(), "→", df_summer.datetime.max())

# ─── Guardar Parquet con todo el verano 2014–24 ────────────────────────
OUT_DIR.mkdir(exist_ok=True)
out_parquet = OUT_DIR / "verano_14-24_long.parquet"
df_summer.to_parquet(out_parquet)
print(f"Guardado Parquet: {df_summer.shape} registros en {out_parquet}")

# ─── Función vectorizada para índice Humidex ───────────────────────────
def humidex(T, RH):
    T_arr  = np.array(T, dtype=float)
    RH_arr = np.array(RH, dtype=float)
    e      = 6.11 * np.exp(5417.753 * (1/273.16 - 1/(T_arr + 273.15))) * (RH_arr/100)
    humid  = T_arr + 0.5555 * (e - 10)
    return pd.Series(humid, index=T.index)

df_summer['Humidex'] = humidex(df_summer['Ta'], df_summer['RH'])
df_summer['hora']   = df_summer.datetime.dt.hour

# ─── Agregaciones para CSV nocturno y diurno ───────────────────────────
noct = df_summer[df_summer.hora.isin(range(0,6))]\
    .groupby('estacion_id')\
    .agg(
      Ta_min_night=('Ta','min'),
      Humidex_mean_night=('Humidex','mean')
    ).reset_index()
noct.to_csv(OUT_DIR/"redmet_nocturno.csv", index=False)
print("Guardado CSV nocturno:", noct.shape, "→ redmet_nocturno.csv")

day = df_summer[df_summer.hora.isin(range(10,17))]
day_agg = day.groupby('estacion_id')\
    .agg(
      Ta_mean_day=('Ta','mean'),
      Ta_p90_day =('Ta', lambda x: x.quantile(0.9)),
      Humidex_mean_day=('Humidex','mean')
    ).reset_index()
day_agg.to_csv(OUT_DIR/"redmet_diurno.csv", index=False)
print("Guardado CSV diurno:", day_agg.shape, "→ redmet_diurno.csv")
