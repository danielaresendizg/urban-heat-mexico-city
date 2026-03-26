# Glosario de términos y nomenclatura

Documento técnico de referencia para la presentación y discusión de tesis.

## 1) Acrónimos institucionales y de plataformas

| Término | Definición |
|---|---|
| CDMX | Ciudad de México. |
| INEGI | Instituto Nacional de Estadística y Geografía. |
| SEDEMA | Secretaría del Medio Ambiente de la CDMX. |
| RedMet | Red de estaciones meteorológicas automáticas de CDMX. |
| GEE | Google Earth Engine. Plataforma de procesamiento geoespacial en la nube. |
| QGIS | Sistema de Información Geográfica de código abierto. |
| UMEP | Urban Multi-scale Environmental Predictor (plugin de QGIS). |
| SOLWEIG | Solar and LongWave Environmental Irradiance Geometry model (dentro de UMEP). |
| OSM | OpenStreetMap. |
| GOB | Google Open Buildings. |

## 2) Variables y métricas térmicas

| Término | Definición |
|---|---|
| LST | Land Surface Temperature (temperatura superficial satelital). |
| Ta | Temperatura del aire. |
| Ta_mean | Promedio estival diurno de Ta. |
| Ta_max | Máximo estival diurno de Ta. |
| UHI_air | Intensidad de isla de calor del aire (anomalía de Ta). |
| UTFVI_air | Urban Thermal Field Variance Index en aire. |
| Tmrt | Mean Radiant Temperature (temperatura radiante media); principal carga radiativa percibida por peatones. |
| UTCI | Universal Thermal Climate Index; índice biometeorológico de estrés térmico. |
| PET | Physiological Equivalent Temperature; índice biometeorológico basado en balance energético humano (MEMI). |
| RH | Relative Humidity (humedad relativa). |
| v10 | Velocidad de viento a 10 m (insumo en UTCI). |
| NDVI | Normalised Difference Vegetation Index (proxy de vegetación). |
| NDBI | Normalised Difference Built-up Index (proxy de superficie construida). |
| Albedo | Fracción de radiación solar reflejada por la superficie. |
| p90 | Percentil 90 (valor alto representativo del 10% más cálido). |

## 3) Nomenclatura de umbrales usados en la tesis

| Umbral | Interpretación operativa |
|---|---|
| Ta >= 26 C | Condición de riesgo térmico diurno (hot26). |
| Ta >= 28 C | Condición térmica extrema (hot28). |
| UTCI >= 32 C | Estrés térmico fuerte. |
| UTCI >= 38 C | Estrés térmico muy fuerte. |
| PET > 41 C | Estrés térmico extremo en espacio exterior. |
| Hazard 0 | Segmentos/manzanas bajo umbral térmico. |
| Hazard 1 | Segmentos/manzanas en 26 a <28 C. |
| Hazard 2 | Segmentos/manzanas en >=28 C. |

## 4) Morfología urbana (Space Matrix)

| Término | Definición |
|---|---|
| FSI | Floor Space Index (intensidad construida). |
| GSI | Ground Space Index (cobertura/sellado de suelo). |
| L (L_equiv) | Número equivalente de niveles (altura media). |
| OSR | Open Space Ratio (espacio abierto relativo). |
| Tipología Space Matrix | Clasificación morfológica derivada de FSI, GSI y L. |
| Compacta continua | Tejido compacto con alta continuidad y alta carga térmica potencial. |
| Perímetro bajo/medio/denso | Bloques perimetrales con distintos niveles de compactación. |
| Barras / Hilera-adosada | Tipologías lineales con exposición variable según orientación y sombra. |
| Mixed/Undetermined | Tipología mixta o de calidad clasificatoria limitada. |


> **Anotación (equivalencia práctica con normativa urbana):** `FSI` es el análogo más cercano a **CUS** y `GSI` al **COS**. `L_equiv` se aproxima a `FSI/GSI`. `OSR` no tiene equivalente directo en CUS/COS. En esta tesis, FSI/GSI son métricas analíticas observadas; CUS/COS son parámetros normativos.

## 5) Configuración espacial (Space Syntax)

| Término | Definición |
|---|---|
| Space Syntax | Marco de análisis configuracional de redes urbanas. |
| Segment map | Red vial segmentada para análisis angular. |
| NAIN | Normalised Angular Integration (integración angular normalizada). |
| NACH | Normalised Angular Choice (elección angular normalizada). |
| r500 / r1000 / r1500 / r5000 | Radios de análisis (escala peatonal, barrial y estructural). |
| Corredor altamente integrado | Tramo con alta integración local y/o barrial, asociado a mayor flujo peatonal potencial. |
| Least-angle path | Trayectoria de menor costo angular (no solo menor distancia métrica). |

## 6) Estadística espacial y modelado

| Término | Definición |
|---|---|
| OLS | Ordinary Least Squares (regresión global). |
| GWR | Geographically Weighted Regression (regresión local con coeficientes espaciales). |
| MGWR | Variante multiescala de GWR (si se implementa en validaciones comparativas). |
| Coeficiente local | Pendiente estimada por unidad espacial en GWR. |
| t-value local | Significancia local del coeficiente GWR. |
| Moran's I | Medida de autocorrelación espacial global en residuos/variables. |
| LISA | Local Indicators of Spatial Association. |
| Bivariada LISA | Asociación espacial local entre dos variables (ej. Ta y vulnerabilidad). |
| Multicolinealidad | Dependencia lineal entre predictores (evaluada con VIF). |
| VIF | Variance Inflation Factor para control de colinealidad. |
| Zero inflation | Exceso de ceros en variables, que afecta inferencia si no se controla. |

## 7) Variables sociales de vulnerabilidad (macro)

| Variable | Lectura |
|---|---|
| 65+ | Población de adultos mayores, mayor sensibilidad fisiológica al calor. |
| 6-14 | Niñez y adolescencia temprana. |
| pct_with_disc | Personas con discapacidad, potencial mayor sensibilidad y barreras de movilidad. |
| pct_no_serv_med | Población sin servicios de salud. |
| pct_pop_sin_auto | Hogares sin automóvil (dependencia de movilidad peatonal/transporte público). |
| pct_elementary_edu | Escolaridad primaria como proxy de desventaja social acumulada. |
| pct_inac | Población económicamente inactiva. |

## 8) Insumos geométricos y microclimáticos

| Término | Definición |
|---|---|
| DEM | Digital Elevation Model (modelo digital de elevación del terreno). |
| DSM | Digital Surface Model (incluye superficie construida/vegetación). |
| SVF | Sky View Factor, fracción de cielo visible desde el punto peatonal. |
| Wall height/aspect | Altura y orientación de fachadas (intercambio radiativo). |
| POI | Point of Interest: punto de muestreo/salida de simulación en corredor. |

## 9) Ecuaciones y símbolos (nomenclatura)

| Símbolo | Significado |
|---|---|
| Ta = 0.5540 * LST + 5.7606 | Función de transferencia local LST->Ta usada en macro. |
| Tmrt = [ (1/sigma) * sum(F_i * (K_i + L_i)) ]^0.25 - 273.15 | Definición radiativa de Tmrt (SOLWEIG). |
| sigma | Constante de Stefan-Boltzmann. |
| F_i | Factor angular de intercambio radiativo. |
| K_i | Flujo de radiación de onda corta. |
| L_i | Flujo de radiación de onda larga. |
| UTCI = f(Ta, Tmrt, v10, RH) | Forma funcional del índice UTCI. |
| PET = f(Ta, Tmrt, v, RH, M, Icl) | Forma funcional del índice PET (MEMI). |
| M | Tasa metabólica en PET. |
| Icl | Aislamiento de vestimenta en PET. |

## 10) Diccionario de campos de la matriz integrada (Appendix F)

Fuente: `latex/appendix/appendix_F.tex` (tabla de data dictionary).

| Campo | Definición |
|---|---|
| `fid` | Internal row identifier |
| `manzana_id` | Unique block identifier |
| `CVEGEO` | Official geo-statistical code |
| `ENTIDAD` | State code (federal entity) |
| `MUN` | Municipality/borough code |
| `NOM_MUN` | Municipality/borough name |
| `pct_0a5` | Population 0--5 (%) |
| `pct_6a14` | Population 6--14 (%) |
| `pct_15a64` | Population 15--64 (%) |
| `pct_65plus` | Population 65+ (%) |
| `pct_ethnic_afro` | Afro-descendant (%) |
| `pct_ethnic_ind` | Indigenous (%) |
| `pct_ethnic_other` | Other ethnicity (%) |
| `rel_dep_0_14` | Dependency ratio (0--14/15--64) |
| `rel_h_m` | Sex ratio (M/F) |
| `pct_with_disc` | With disability (%) |
| `pct_without_disc` | Without disability (%) |
| `pct_no_school` | No schooling (%) |
| `pct_elementary_edu` | Primary completed (%) |
| `pct_elementary2_edu` | Secondary completed (%) |
| `pct_more_edu` | Higher education (%) |
| `pct_ocup` | Employed (%) |
| `pct_desocup` | Unemployed (%) |
| `pct_inac` | Inactive (%) |
| `pct_serv_med` | With health service (%) |
| `pct_no_serv_med` | Without health service (%) |
| `pct_pop_sin_auto` | Households without car (%) |
| `pct_pop_auto` | Households with car (%) |
| `Ta_mean` | Mean summer daytime air temp. |
| `Ta_max` | Max summer daytime air temp. |
| `UHI_mean` | Mean UHI intensity |
| `UHI_max` | Max UHI intensity |
| `LST_mean` | Mean land surface temp. |
| `NDVI_mean` | Mean NDVI |
| `NDBI_mean` | Mean NDBI |
| `Albedo_mean` | Mean broadband albedo |
| `A_m2` | Gross built floor area |
| `B_m2` | Gross block land area |
| `sup_const_tot_m2` | Total constructed floor area |
| `sup_terreno_tot_m2` | Total land plot area |
| `n_props` | Number of property records |
| `n_predios` | Number of parcels |
| `FSI` | Floor Space Index |
| `GSI` | Ground Space Index |
| `L_equiv` | Equivalent number of floors |
| `OSR` | Open Space Ratio |
| `coef_Intercept` | GWR intercept coefficient |
| `coef_pct_pop_sin_auto` | Coef. % without car |
| `coef_pct_no_serv_med` | Coef. % without health |
| `coef_pct_inac` | Coef. % inactive |
| `coef_pct_65plus` | Coef. % 65+ |
| `coef_pct_6a14` | Coef. % 6--14 |
| `coef_pct_with_disc` | Coef. % disability |
| `coef_pct_elementary_edu` | Coef. % primary edu |
| `tval_Intercept` | t-stat intercept |
| `tval_pct_pop_sin_auto` | t-stat % without car |
| `tval_pct_no_serv_med` | t-stat % without health |
| `tval_pct_inac` | t-stat % inactive |
| `tval_pct_65plus` | t-stat % 65+ |
| `tval_pct_6a14` | t-stat % 6--14 |
| `tval_pct_with_disc` | t-stat % disability |
| `tval_pct_elementary_edu` | t-stat % primary edu |
| `is_hot_26` | Block Ta >= 26 C |
| `is_hot_28` | Block Ta >= 28 C |
| `hot26_pct_65plus` | 65+ sig. at 26 C |
| `hot28_pct_65plus` | 65+ sig. at 28 C |
| `hot26_pct_6a14` | 6--14 sig. at 26 C |
| `hot28_pct_6a14` | 6--14 sig. at 28 C |
| `hot26_any_social` | Any social sig. at 26 C |
| `hot28_any_social` | Any social sig. at 28 C |
| `hot26_count_social` | Count sig. social at 26 C |
| `hot28_count_social` | Count sig. social at 28 C |
| `peligro_cat` | Heat hazard class |
| `typology_code_base` | Base SpaceMatrix code |
| `typology_name_base` | Base typology label |
| `typology_code_final` | Final typology code |
| `typology_sm_final` | Final SpaceMatrix label |
| `flag_mixto_dq` | Mixed/low-quality flag |
| `flag_mixto_limite` | Near class boundary flag |
| `diag_reason` | Diagnostic for class change |
| `street_len_in_manz_m` | Street length bordering block |
| `NACHr500m_lenw_mean` | Betweenness 500m |
| `NACHr1000m_lenw_mean` | Betweenness 1000m |
| `NACHr1500m_lenw_mean` | Betweenness 1500m |
| `NACHr5000m_lenw_mean` | Betweenness 5000m |
| `NAINr500m_lenw_mean` | Integration 500m |
| `NAINr1000m_lenw_mean` | Integration 1000m |
| `NAINr1500m_lenw_mean` | Integration 1500m |
| `NAINr5000m_lenw_mean` | Integration 5000m |
| `NACHr500m_near` | Betweenness nearest hot seg. |
| `NAINr500m_near` | Integration nearest hot seg. |
| `peligro_cat_near` | Heat class nearest seg. |
| `_dist` | Distance to nearest hot seg. |
| `hot_cat_manz` | Block heat category |
| `is_hotspot` | Block is hotspot |

## 11) Referencias metodológicas directas en la tesis

- `latex/main/methodology.tex`
- `latex/main/results_macro.tex`
- `latex/main/results_meso.tex`
- `latex/main/results_micro.tex`
- `latex/appendix/appendix_F.tex`
