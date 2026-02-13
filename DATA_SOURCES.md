# Data Sources and Availability

This document explains how to access all datasets used in this dissertation for full reproducibility.

## Data Sharing Strategy

Due to GitHub's file size limitations (files > 100MB), large geospatial datasets are hosted on Google Drive. This is standard practice for computational research with large datasets.

## Dataset Categories

### 1. **Included in Repository** (GitHub)
Small reference files and metadata (< 10MB total):

- `data/sample/redmet_stations.csv` - RedMet weather station metadata
- `data/sample/redmet_diurnal_2014-2024.csv` - Air temperature aggregations
- Supporting CSV files for statistical outputs

### 2. **External Data (Google Drive)**
Large processed datasets (2.3 GB total):

#### **A. RedMet Historical Data** (89 MB)
**Source:** SEDEMA-CDMX (Sistema de Monitoreo Atmosférico)
**Access:** [Google Drive - RedMet](https://drive.google.com/drive/folders/YOUR_FOLDER_ID_HERE?usp=sharing)
**Contents:**
- Historical XLS files (2014-2024): Temperature and Humidity
- Processed summer timeseries
- Station geometries (GPKG)

**Alternative:** Download directly from [SEDEMA-CDMX Data Portal](http://www.aire.cdmx.gob.mx/default.php?opc='aKBhnmI=')

#### **B. Space Matrix Dataset** (1.6 GB)
**Source:** Derived from INEGI census blocks + Google Open Buildings
**Access:** [Google Drive - Space Matrix](https://drive.google.com/drive/folders/YOUR_FOLDER_ID_HERE?usp=sharing)
**Contents:**
- FSI, GSI, L, OSR morphological indicators
- Building footprint geometries
- Census block (manzana) level aggregations

**Original Sources:**
- [INEGI Census 2020](https://www.inegi.org.mx/programas/ccpv/2020/)
- [Google Open Buildings](https://sites.research.google/open-buildings/)

#### **C. Street Network** (216 MB)
**Source:** OpenStreetMap + Space Syntax analysis
**Access:** [Google Drive - Street Network](https://drive.google.com/drive/folders/YOUR_FOLDER_ID_HERE?usp=sharing)
**Contents:**
- Cleaned street network geometries
- NAIN/NACH centralities at multiple radii (500m, 1000m, 1500m, 5000m)
- Segment map outputs from DepthmapX

**Original Source:**
- [OpenStreetMap](https://www.openstreetmap.org/) - Mexico City extract
- Processed with [DepthmapX 0.8.0](https://github.com/SpaceGroupUCL/depthmapX)

#### **D. Census Blocks (Manzanas)** (357 MB)
**Source:** INEGI 2020
**Access:** [Google Drive - Manzanas](https://drive.google.com/drive/folders/YOUR_FOLDER_ID_HERE?usp=sharing)
**Contents:**
- Census block geometries (poligono_manzanas_cdmx)
- Socioeconomic indicators
- Population statistics
- Aggregated thermal and morphological variables

**Original Source:**
- [INEGI Marco Geoestadístico 2020](https://www.inegi.org.mx/temas/mg/)

#### **E. UMEP Microclimate Outputs** (48 MB)
**Source:** SOLWEIG simulations via QGIS UMEP plugin
**Access:** [Google Drive - UMEP](https://drive.google.com/drive/folders/YOUR_FOLDER_ID_HERE?usp=sharing)
**Contents:**
- Mean Radiant Temperature (Tmrt) rasters
- UTCI (Universal Thermal Climate Index) outputs
- PET (Physiological Equivalent Temperature) outputs
- Study area microclimate simulations (typical summer day)

**Processing Software:**
- [QGIS 3.34](https://qgis.org/)
- [UMEP Plugin](https://umep-docs.readthedocs.io/)
- [SOLWEIG Model](https://umep-docs.readthedocs.io/en/latest/OtherManuals/SOLWEIG.html)

#### **F. Thermal Data (Calor)** (15 MB)
**Source:** Landsat 8/9 via Google Earth Engine
**Access:** [Google Drive - Calor](https://drive.google.com/drive/folders/YOUR_FOLDER_ID_HERE?usp=sharing)
**Contents:**
- LST (Land Surface Temperature) climatology (2014-2024)
- Calibrated air temperature (Ta) estimates
- UHI intensity (UHI_air)
- UTFVI (Urban Thermal Field Variance Index)
- NDVI, NDBI, Albedo auxiliary layers

**Processing Code:**
- See `code/gee/landsat_thermal_climatology.js`
- Calibration regression: Ta = 0.554 × LST + 5.761

#### **G. Administrative Boundaries** (172 KB)
**Source:** INEGI 2020
**Access:** [Google Drive - Boundaries](https://drive.google.com/drive/folders/YOUR_FOLDER_ID_HERE?usp=sharing)
**Contents:**
- CDMX.gpkg - Mexico City boundary
- manzana_level.gpkg - Census block boundaries
- AGEB polygons (urban/rural)
- Alcaldías (municipality) boundaries

**Original Source:**
- [INEGI Marco Geoestadístico 2020](https://www.inegi.org.mx/temas/mg/)

### 3. **Publicly Available Data (No Download Needed)**

These datasets can be accessed directly through web interfaces or APIs:

#### **Google Earth Engine Assets**
- Landsat 8/9 Collection 2 (USGS)
- SRTM Digital Elevation Model
- Access via: [Google Earth Engine Code Editor](https://code.earthengine.google.com/)
- See: `code/gee/landsat_thermal_climatology.js`

#### **INEGI Census Data**
- 2020 Population and Housing Census
- Socioeconomic indicators
- Download from: [INEGI Data Portal](https://www.inegi.org.mx/programas/ccpv/2020/)

#### **OpenStreetMap**
- Mexico City street network
- Building footprints
- Download from: [Geofabrik](https://download.geofabrik.de/north-america/mexico.html)

## How to Reproduce This Research

### Option 1: Use Processed Data (Recommended)
1. Download processed datasets from Google Drive links above
2. Update file paths in Python scripts to point to your download location
3. Run analysis scripts in `code/python/` directory

### Option 2: Process from Raw Sources
1. Download raw data from original sources (INEGI, OSM, etc.)
2. Run preprocessing scripts: `code/python/preprocessing/`
3. Run GEE script: `code/gee/landsat_thermal_climatology.js`
4. Process spatial layers with DepthmapX and QGIS UMEP
5. Run analysis scripts

## Data Size Reference

| Dataset Category | Size | Repository Location |
|------------------|------|-------------------|
| GitHub (code + docs) | ~5 MB | This repository |
| Sample data (GitHub) | ~10 MB | `data/sample/` |
| **Google Drive (processed data)** | **2.3 GB** | Links above |
| Raw source data (if downloaded) | ~5-10 GB | See original sources |

## Citation

If you use these datasets, please cite:

```bibtex
@mastersthesis{resendiz2025urban,
  author       = {Resendiz Garcia, Daniela},
  title        = {Coupling Remote Sensing, Morphology, and Microclimate Simulation
                  to Analyse Urban Heat in Mexico City, Mexico},
  school       = {UCL The Bartlett School of Architecture},
  year         = {2025},
  type         = {{MSc} Dissertation},
  url          = {https://github.com/danielaresendizg/urban-heat-mexico-city}
}
```

For specific datasets, also cite the original sources listed above (INEGI, SEDEMA-CDMX, Google Open Buildings, etc.).

## Data Privacy and Ethics

All datasets used are either:
- Publicly available government data (INEGI, SEDEMA)
- Open data (OpenStreetMap, Google Open Buildings)
- Aggregated census statistics (no individual-level data)

No personal or sensitive information is included in any dataset.

## Questions?

For questions about data access or processing:
- Open an issue in this repository
- Contact: [Your email or contact info]

## Data Archive

For long-term preservation, these datasets will be deposited in:
- **Zenodo** (with DOI) - [Link to be added after deposit]
- **UCL Research Data Repository** - [Link to be added]

This ensures permanent availability beyond the lifetime of Google Drive links.
