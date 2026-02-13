# Google Earth Engine Scripts

This folder contains JavaScript code for Google Earth Engine to process Landsat 8/9 imagery and generate thermal surfaces for Mexico City.

## Script: `landsat_thermal_climatology.js`

**Purpose:** Multi-annual summer climatology (2014-2024) for Mexico City thermal analysis

### Methodology

1. **Data Source:** Landsat 8/9 Collection 2 Level-2 (surface reflectance + thermal)
2. **Period:** Summer months (June-August) for each year 2014-2024
3. **AOI:** Mexico City metropolitan area (19.1°-19.7°N, 98.9°-99.4°W)
4. **Resolution:** 30m spatial resolution
5. **Cloud filtering:** Cloud cover < 20%

### Processing Steps

1. **Preprocessing:**
   - Optical band scaling (×0.0000275 - 0.2)
   - Thermal band scaling (×0.00341802 + 149.0) → Kelvin
   - QA masking for clouds, shadows, cirrus

2. **Climatology:**
   - Median composite per summer (June-August)
   - Multi-year mean across 2014-2024

3. **Spectral Indices:**
   - **NDVI** (vegetation): (NIR - Red) / (NIR + Red)
   - **NDBI** (built-up): (SWIR1 - NIR) / (SWIR1 + NIR)
   - **Albedo** (mean): Average of blue, green, red bands

4. **Thermal Variables:**
   - **LST (Land Surface Temperature):** Brightness temperature corrected for emissivity
     - Emissivity derived from NDVI-based fractional vegetation cover
   - **Ta (Air Temperature):** LST-to-Ta calibration using local weather stations
     - Ta = 0.554 × LST + 5.761 (from RedMet station calibration)
   - **UHI_air (Urban Heat Island):** Z-score of Ta (spatial standardization)
   - **UTFVI_air (Urban Thermal Field Variance Index):** (Ta - Ta_mean) / Ta

### Outputs

**Climatology (2014-2024 average):**
- `NDVI_clim.tif`
- `NDBI_clim.tif`
- `Albedo_clim.tif`
- `LST_day_clim.tif`
- `Ta_clim.tif`
- `UHI_air_clim.tif`
- `UTFVI_air_clim.tif`

**Annual layers (per year 2014-2024):**
- `LST_day_{year}.tif`
- `Ta_clim_{year}.tif`
- `UHI_air_{year}.tif`
- `UTFVI_air_{year}.tif`

All outputs exported to Google Drive folder `CDMX_Thermal_Methodology/`

### How to Use

1. Open [Google Earth Engine Code Editor](https://code.earthengine.google.com/)
2. Copy and paste the script
3. Run the script (green "Run" button)
4. Check the **Tasks** tab (right panel) to export layers to Google Drive
5. Click "Run" on each export task

### References

- **Chakraborty et al. (2022):** Optical and thermal band scaling methodology
- **Jesdale et al. (2013):** NDVI/NDBI spectral indices
- **Waleed et al. (2023):** UTFVI methodology
- **Gorelick et al. (2017):** Google Earth Engine platform

### Integration with Python/R Workflows

Exported rasters are used as inputs for:
- **Macro-scale analysis** (Python scripts in `code/python/macro/`)
- **GWR modeling** (R scripts in `code/r/`)
- **Hotspot detection** and vulnerability mapping

See main repository README for full analysis pipeline.
