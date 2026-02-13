# Data

This folder contains sample data files for the analysis. Full datasets are stored in Google Drive due to size constraints.

## Sample Data (included in repository)

- `sample/` - Small CSV files for reference and testing
  - `redmet_stations.csv` - RedMet weather station metadata
  - `redmet_diurnal_2014-2024.csv` - Diurnal temperature aggregations
  - Vulnerability indicators and statistical outputs

## Full Datasets (Google Drive)

Due to GitHub file size limitations, full datasets are hosted on Google Drive:

### RedMet Historical Data (2014-2024)
**Location:** `dissertation_data/redmet/`
**Access:** [Google Drive Link - To be added]
**Contents:**
- `Estaciones_historico_14-24/` - Historical XLS files by year
  - `14REDMET/` through `24REDMET/`
  - Temperature (TMP.xls) and Humidity (RH.xls) files
- `procesados/` - Processed outputs
  - `verano_14-24_long.parquet` - Full summer timeseries
  - `redmet_diurnal.csv` - Diurnal aggregations
  - `redmet_nocturnal.csv` - Nocturnal aggregations
- `estaciones_operacion_CDMX.gpkg` - Station geometries
- `scripts/` - Processing scripts (also in `code/python/preprocessing/`)

### How to Access Google Drive Data

1. **Click the Google Drive link** above (once added)
2. **Download the entire folder** or specific files you need
3. **Update file paths** in the scripts to point to your local download location

### Setting up the data for `01_process_redmet_stations.py`

```python
# Update these paths in the script:
BASE     = Path("/path/to/your/downloaded/redmet")
CSV_EST  = BASE / "estaciones_operacion_CDMX.csv"
GPKG_EST = BASE / "estaciones_operacion_CDMX.gpkg"
HIST_DIR = BASE / "Estaciones_historico_14-24"
OUT_DIR  = BASE / "procesados"
```

## Data Sources & Credits

- **RedMet Network:** SEDEMA-CDMX (Sistema de Monitoreo Atmosférico de la Ciudad de México)
- **Census Data:** INEGI 2020 (Instituto Nacional de Estadística y Geografía)
- **Satellite Data:** Landsat 8/9 via Google Earth Engine
- **Building Footprints:** Google Open Buildings
- **Cadastral Data:** IPDP-CDMX (Instituto de Planeación Democrática y Prospectiva)

## Data Use & Attribution

If you use this data in your research, please cite:

```
Resendiz Garcia, D. (2025). Coupling Remote Sensing, Morphology, and Microclimate Simulation
to Analyse Urban Heat in Mexico City, Mexico. MSc Dissertation, UCL The Bartlett School of
Architecture.
```

For RedMet data specifically:
```
SEDEMA-CDMX. (2024). Red de Meteorología y Radiación Solar de la Ciudad de México (RedMet).
Sistema de Monitoreo Atmosférico. https://www.aire.cdmx.gob.mx/
```
