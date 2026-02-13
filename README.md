# Coupling Remote Sensing, Morphology, and Microclimate Simulation to Analyse Urban Heat in Mexico City

**MSc Dissertation** | Space Syntax: Architecture and Cities | UCL The Bartlett School of Architecture | 2024-25

**Author:** Daniela Resendiz Garcia
**Supervisor:** Dr. Kimon Krenz

---

## Abstract

This dissertation proposes a city-to-street analytical pipeline to assess urban heat exposure in Mexico City by coupling satellite-derived thermal surfaces, urban morphology, street-network configuration, and microclimate simulation. The study addresses three research questions across three nested spatial scales:

- **Q1 (Macro):** Where do daytime summer air temperatures co-locate with socially vulnerable populations?
- **Q2 (Meso):** Which combinations of urban form/density and network configuration characterise thermal-social hotspots?
- **Q3 (Micro):** How can micro-scale thermal stress be assessed to define passive design targets for heat reduction?

## Methodology

The analysis is structured across three scales:

| Scale | Methods | Key Outputs |
|-------|---------|-------------|
| **Macro** | Landsat 8/9 LST-to-Ta calibration (GEE), GWR by municipality | UHI air maps, thermal-social hotspots |
| **Meso** | Space Syntax (NAIN/NACH), Space Matrix (FSI/GSI/L/OSR) | Contiguous clusters of heat severity + accessibility |
| **Micro** | UMEP/SOLWEIG simulation (Tmrt, UTCI, PET) | Passive design targets for pedestrian corridors |

### Key Data Sources

- **Thermal:** Landsat 8/9 (2014-2024 summers), RedMet weather stations (SEDEMA-CDMX)
- **Social:** 2020 Mexican Population and Housing Census (INEGI) at block level
- **Morphology:** Google Open Buildings, cadastral data (IPDP-CDMX)
- **Network:** Segmented street graph with angular centralities at 500, 1000, 1500, 5000 m

## Repository Structure

```
urban-heat-mexico-city/
├── README.md
├── LICENSE
├── .gitignore
│
├── code/
│   ├── python/                  # Python analysis scripts
│   │   ├── hotspots_heat+social.py
│   │   ├── hotspots_space_syntax.py
│   │   ├── compare_OLS_GWR_moran.py
│   │   ├── segment_thermal.py
│   │   ├── generate_figures.py
│   │   └── ...
│   ├── r/                       # R spatial regression scripts
│   │   └── regresion_spatial_lit.R
│   └── gee/                     # Google Earth Engine scripts
│       └── (GEE code description)
│
├── data/
│   └── sample/                  # Sample/reference data files
│
├── latex/
│   ├── main/                    # Main dissertation LaTeX source
│   └── appendix/                # Appendices LaTeX source
│
├── figures/                     # Key result figures
│
└── qgis/                        # QGIS style files (.qml)
```

## Software and Tools

- **Google Earth Engine** - Satellite imagery processing and thermal mapping
- **Python 3.x** - Spatial analysis, GWR, statistical testing
  - `geopandas`, `pysal`, `mgwr`, `matplotlib`, `numpy`, `scipy`
- **R** - Spatial regression (OLS, GWR, Moran's I)
  - `sf`, `spdep`, `spatialreg`, `GWmodel`
- **QGIS + DepthmapX** - Space Syntax analysis, network modelling
- **UMEP/SOLWEIG** - Microclimate simulation (Tmrt, UTCI, PET)
- **LaTeX** - Document preparation

## Key Findings

1. **Tmrt** is the most appropriate indicator of pedestrian heat stress in Mexico City
2. Thermal exposure and social vulnerability clearly overlap at sub-municipal scales
3. Two distinct spatial mechanisms were identified:
   - **Structural heat** in compact, low-vegetation areas (high GSI, low OSR)
   - **Corridor heat** along highly integrated pedestrian axes (high NAIN)
4. Passive strategies (continuous shade, ventilation, cool non-glare materials) can substantially reduce outdoor heat stress

## Citation

If you use this work, please cite:

```
Resendiz Garcia, D. (2025). Coupling Remote Sensing, Morphology, and Microclimate Simulation
to Analyse Urban Heat in Mexico City, Mexico. MSc Dissertation, UCL The Bartlett School of
Architecture.
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

Daniela Resendiz Garcia - [GitHub](https://github.com/danielaresendizg)
