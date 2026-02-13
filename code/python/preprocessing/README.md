# Preprocessing Scripts

Data preprocessing scripts for thermal and meteorological data inputs to the main analysis.

## Script: `01_process_redmet_stations.py`

**Purpose:** Process RedMet (Mexico City Automatic Weather Station Network) historical data (2014-2024) to generate station-level summaries for LST→Ta calibration.

### Data Source

**RedMet Network** (SEDEMA-CDMX): Automatic weather stations measuring air temperature (Ta) and relative humidity (RH) at hourly resolution across Mexico City.

### Processing Steps

1. **Load station metadata**
   - `estaciones_operacion_CDMX.csv` - Station locations and IDs
   - `estaciones_operacion_CDMX.gpkg` - Station geometries

2. **Process historical XLS files (2014-2024)**
   - Convert wide-format `.xls` files to long format
   - Merge temperature (TMP) and humidity (RH) data
   - Filter valid station IDs

3. **Clean and filter**
   - Remove error codes (-99, -999)
   - Filter summer months only (June-August)
   - Quality control checks

4. **Calculate Humidex**
   - Apparent temperature accounting for humidity
   - Humidex = Ta + 0.5555 × (e - 10)
   - Where e is vapor pressure from Ta and RH

5. **Aggregate statistics**
   - **Nocturnal (00:00-06:00):**
     - Ta_min_night
     - Humidex_mean_night
   - **Diurnal (10:00-17:00):**
     - Ta_mean_day
     - Ta_p90_day (90th percentile)
     - Humidex_mean_day

### Outputs

- `verano_14-24_long.parquet` - Full summer timeseries (2014-2024)
- `redmet_nocturno.csv` - Nocturnal aggregations by station
- `redmet_diurno.csv` - Diurnal aggregations by station

### LST→Ta Calibration

The diurnal air temperature data (`redmet_diurno.csv`) is used to calibrate Land Surface Temperature (LST) from Landsat to air temperature (Ta) for use in Google Earth Engine.

**Calibration regression (derived from spatial overlay of LST and station Ta):**
```
Ta = 0.554 × LST + 5.761
R² = [see dissertation Chapter 3]
```

This city-specific transfer function accounts for:
- High-altitude conditions (~2,240 m elevation)
- Low humidity environment
- Urban surface heterogeneity
- Summer daytime conditions (10:00-14:00)

### Dependencies

```python
import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
```

### Usage

```bash
python 01_process_redmet_stations.py
```

**Note:** Requires access to RedMet historical XLS files (not included in repository due to size). Contact SEDEMA-CDMX or author for access.

### Integration with GEE Workflow

The calibration coefficients are used in:
- `code/gee/landsat_thermal_climatology.js` (lines 13-14)
- Python macro scripts for thermal variable processing

### References

- **Chakraborty et al. (2022):** Humidity effects on LST-Ta relationships
- **Magaña & Vargas (2020):** Mexico City heat thresholds
- **SEDEMA-CDMX:** RedMet network specifications
