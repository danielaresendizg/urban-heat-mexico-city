/******************************************************
  CDMX – Climatología y Serie Temporal de Calor
  CDMX – Climatology and Heat Time Series
  (Veranos 2014–2024, índice multibanda y exportación por año)

  Methodology:
  - Multi-annual summer composite (June-August, 2014-2024)
  - Landsat 8/9 Collection 2 Level-2 processing
  - LST-to-air-temperature calibration using local weather stations
  - NDVI, NDBI, albedo, LST, Ta, UHI_air, UTFVI_air computation
  - Export to Google Drive for integration with Python/R workflows

  References:
  - Chakraborty et al. (2022) - LST scaling methodology
  - Jesdale et al. (2013) - NDVI/NDBI indices
  - Waleed et al. (2023) - UTFVI methodology
******************************************************/

// 1) Definición del Área de Interés (AOI) / Define Area of Interest
var aoi = ee.Geometry.Polygon([
  [[-99.400, 19.100],[-99.400, 19.700],
   [-98.900, 19.700],[-98.900, 19.100]]
]);
Map.centerObject(aoi, 9); // Centra el mapa / Center the map

// 2) Parámetros globales / Global parameters
var scale      = 30;                         // Resolución espacial en metros / Spatial resolution (m)
var folderBase = 'CDMX_Thermal_Methodology'; // Carpeta Drive / Export folder in Drive
var years      = ee.List.sequence(2014, 2024);
var coef_a     = 0.554038;                   // Pendiente regresión LST→Ta (de tu CSV) / Slope from LST→Ta regression
var coef_b     = 5.760580;                   // Intercepto regresión LST→Ta / Intercept from LST→Ta regression

// 3) Función de preprocesado / Preprocess function
//    - scaleSRST: aplica factores de escala a bandas ópticas y térmicas
//      Applies reflectance and brightness temperature scaling
//      (basado en Chakraborty et al. 2022)
//    - maskQA: enmascara píxeles con nubes, sombras y cirros
//      Masks cloudy/shadowy pixels using QA_PIXEL bits (nubes bit5, sombra bit3, cirros bit4)
//      (metodología estándar Landsat Level-2)
function preprocess(image) {
  // Escala ópticas / Optical bands scaling
  var optical = image.select('SR_B.*')
                     .multiply(0.0000275).add(-0.2);
  // Escala térmicas / Thermal band scaling (DN→Kelvin)
  var thermal = image.select('ST_B.*')
                     .multiply(0.00341802).add(149.0);
  image = image.addBands(optical, null, true)
               .addBands(thermal, null, true);
  // QA mask / Mask cloudy/shadow/cirrus
  var qa   = image.select('QA_PIXEL');
  var mask = qa.bitwiseAnd(1<<5).eq(0)
             .and(qa.bitwiseAnd(1<<3).eq(0))
             .and(qa.bitwiseAnd(1<<4).eq(0));
  return image.updateMask(mask);
}

// 4) Generación de climatología multianual / Multi-annual summer climatology
//    Crea un composite por cada verano y luego promedia todos los años
var allLandsat = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
                    .merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'));
var summerComposites = years.map(function(y) {
  var start = ee.Date.fromYMD(y,6,1);
  var end   = ee.Date.fromYMD(y,8,31);
  return allLandsat
    .filterBounds(aoi)
    .filterDate(start, end)
    .filter(ee.Filter.lt('CLOUD_COVER',20))
    .map(preprocess)
    .median()
    .set('year', y);
});
var summerClim = ee.ImageCollection(summerComposites).mean();
// summerClim: promedio de todos los composites estivales (2014–2024)

// 5) Cálculo de índices espectrales / Spectral indices
//    NDVI (vegetación) y NDBI (área construida) según Jesdale et al. 2013
var ndvi   = summerClim.normalizedDifference(['SR_B5','SR_B4']).rename('NDVI_clim');
var ndbi   = summerClim.normalizedDifference(['SR_B6','SR_B5']).rename('NDBI_clim');
//    Albedo medio / Mean albedo
var albedo = summerClim.select(['SR_B2','SR_B3','SR_B4'])
                       .reduce(ee.Reducer.mean())
                       .rename('Albedo_clim');

// 6) Cálculo de LST diurna / Daytime LST (°C)
//    Emisividad basada en NDVI (metodología S0169204624002548)
var fv    = ndvi.subtract(-1).divide(1 - -1).pow(2); // simplificación de ndvi.unitScale
var em    = fv.multiply(0.004).add(0.986);
var LST_day = summerClim.select('ST_B10').expression(
  '(tb / (1 + ((11.5 * (tb / 14380)) * log(em)))) - 273.15',
  { tb: summerClim.select('ST_B10'), em: em }
).rename('LST_day_clim');

// 7) Predicción temperatura del aire / Predicted air temperature
//    Ta_clim = a * LST_day + b (regresión desde CSV de calibración)
var Ta_clim = LST_day.expression(
  'a * lst + b',
  { lst: LST_day, a: coef_a, b: coef_b }
).rename('Ta_clim');

// 8) Cálculo UHI_air y UTFVI_air climáticos / Climatic UHI and UTFVI
//    UHI_air = z-score espacial de Ta_clim (Local Climate Zones paper S2352938521002019)
var stats = Ta_clim.reduceRegion({
  reducer: ee.Reducer.mean().combine({ reducer2: ee.Reducer.stdDev(), sharedInputs: true }),
  geometry: aoi, scale: scale, maxPixels: 1e13
});
var Ta_mean = ee.Number(stats.get('Ta_clim_mean'));
var Ta_std  = ee.Number(stats.get('Ta_clim_stdDev'));
var UHI_clim = Ta_clim.subtract(Ta_mean).divide(Ta_std).rename('UHI_air_clim');

//    UTFVI_air = (Ta_clim − Ta_mean) / Ta_clim (UTFVI methodology)
var UTFVI_clim = Ta_clim.subtract(Ta_mean).divide(Ta_clim).rename('UTFVI_air_clim');

// 9) Visualización de capas / Layer visualization
Map.addLayer(ndvi,       {min:-0.2, max:0.8, palette:['blue','white','green']},     'NDVI_clim');
Map.addLayer(ndbi,       {min:-0.2, max:0.8, palette:['white','red']},              'NDBI_clim');
Map.addLayer(albedo,     {min:0.1,  max:0.4},                                       'Albedo_clim');
Map.addLayer(LST_day,    {min:20,   max:35,  palette:['040274','fed976','ff0000']}, 'LST_day_clim (°C)');
Map.addLayer(Ta_clim,    {min:18,   max:30},                                        'Ta_clim (°C)');
Map.addLayer(UHI_clim,   {min:-2,   max:2,   palette:['blue','white','red']},       'UHI_air_clim');
Map.addLayer(UTFVI_clim, {min:-0.5, max:0.2, palette:['blue','white','red']},       'UTFVI_air_clim');

// 10) Export each raster separately
var layers = [
  {image: ndvi, name: 'NDVI_clim'},
  {image: ndbi, name: 'NDBI_clim'},
  {image: albedo, name: 'Albedo_clim'},
  {image: LST_day, name: 'LST_day_clim'},
  {image: Ta_clim, name: 'Ta_clim'},
  {image: UHI_clim, name: 'UHI_air_clim'},
  {image: UTFVI_clim, name: 'UTFVI_air_clim'}
];

layers.forEach(function(layer) {
  Export.image.toDrive({
    image: layer.image.toFloat(),
    description: layer.name,
    fileNamePrefix: layer.name,
    folder: folderBase,
    region: aoi,
    scale: scale,
    crs: 'EPSG:4326',
    maxPixels: 1e13
  });
});

// 11) Exportación de capas anuales / Export per-year layers for backup
years.evaluate(function(list) {
  list.forEach(function(y) {
    var start = ee.Date.fromYMD(y,6,1);
    var end   = ee.Date.fromYMD(y,8,31);
    var summer = allLandsat
      .filterBounds(aoi)
      .filterDate(start, end)
      .filter(ee.Filter.lt('CLOUD_COVER',20))
      .map(preprocess)
      .median();
    var LST_y = summer.select('ST_B10').expression(
      '(tb / (1 + ((11.5*(tb/14380))*log(em)))) - 273.15',
      { tb: summer.select('ST_B10'), em: em }
    ).rename('LST_day_' + y);
    var Ta_y = LST_y.expression('a * lst + b',
      { lst: LST_y, a: coef_a, b: coef_b }
    ).rename('Ta_clim_' + y);
    var statsY = Ta_y.reduceRegion({
      reducer: ee.Reducer.mean().combine({ reducer2: ee.Reducer.stdDev(), sharedInputs:true }),
      geometry: aoi, scale: scale, maxPixels: 1e13
    });
    var mY = ee.Number(statsY.get('Ta_clim_' + y + '_mean')),
        sY = ee.Number(statsY.get('Ta_clim_' + y + '_stdDev'));
    var UHI_y  = Ta_y.subtract(mY).divide(sY).rename('UHI_air_' + y);
    var UTFVI_y= Ta_y.subtract(mY).divide(Ta_y).rename('UTFVI_air_' + y);

    // Export each layer
    Export.image.toDrive({image: LST_y,  description: 'LST_day_' + y,   fileNamePrefix: 'LST_day_' + y,   folder:folderBase, region:aoi, scale:scale, crs:'EPSG:4326', maxPixels:1e13});
    Export.image.toDrive({image: Ta_y,   description: 'Ta_clim_' + y,   fileNamePrefix: 'Ta_clim_' + y,   folder:folderBase, region:aoi, scale:scale, crs:'EPSG:4326', maxPixels:1e13});
    Export.image.toDrive({image: UHI_y,  description: 'UHI_air_' + y,  fileNamePrefix: 'UHI_air_' + y,  folder:folderBase, region:aoi, scale:scale, crs:'EPSG:4326', maxPixels:1e13});
    Export.image.toDrive({image: UTFVI_y,description: 'UTFVI_air_' + y,fileNamePrefix: 'UTFVI_air_' + y,folder:folderBase, region:aoi, scale:scale, crs:'EPSG:4326', maxPixels:1e13});
  });
});

print('Script completado. Verifica la pestaña Tasks para exportar las capas.');
print('Script completed. Check the Tasks tab to export layers.');
