# --- 1. Librerías ---
cat("Cargando librerías necesarias...\n")
library(sf)
library(spdep)
library(spatialreg)
library(GWmodel)
library(dplyr)
library(tmap)

# --- 2. Leer datos ---
cat("Leyendo archivo de manzanas...\n")
ruta <- "/home/ucbvdre/Scratch/heat_cdmx/manzanas_IVS_heat_20250707_sin_nulos.gpkg"
tryCatch({
  gdf <- st_read(ruta, quiet = TRUE)
}, error = function(e) {
  stop("❌ Error al leer el archivo GPKG: ", e$message)
})

# --- 3. Variables óptimas según lo discutido ---
vars <- c(
  "Ta_max", "NDVI_mean",
  "pct_0a5", "pct_60plus", "pct_hli", "pct_afro", "pct_disc", "pct_inac", "pct_no_serv_med",
  "vul_PRO_OCUP_C", "vul_GRAPROES"
)
cat("Verificando variables...\n")
faltantes <- setdiff(vars, names(gdf))
if(length(faltantes) > 0) warning("⚠️ Variables faltantes en el shapefile: ", paste(faltantes, collapse = ", "))
vars <- vars[vars %in% names(gdf)]
gdf <- gdf |> select(any_of(vars)) |> na.omit()

cat("Validando geometría/proyección...\n")
if(st_is_longlat(gdf)) stop("❌ Transforma tu geometría a un CRS proyectado (en metros): gdf <- st_transform(gdf, 32614)")
if(any(!st_is_valid(gdf))) {
  cat("Corrigiendo geometrías inválidas...\n")
  gdf <- st_make_valid(gdf)
}

# --- 4. Matriz de pesos espaciales (KNN, k=8) ---
cat("Calculando matriz de pesos espaciales...\n")
coords <- st_coordinates(st_centroid(gdf))
knn <- knearneigh(coords, k=8)
nb <- knn2nb(knn)
lw <- nb2listw(nb, style = "W")

# --- 5. Fórmula de regresión ---
cat("Definiendo la fórmula de regresión...\n")
fmla <- as.formula(
  paste("Ta_max ~", paste(vars[vars != "Ta_max" & vars != "geometry"], collapse = " + "))
)

# --- 6. OLS clásico ---
cat("Ajustando modelo OLS...\n")
ols <- lm(fmla, data = gdf)
summary_ols <- summary(ols)

# --- 7. Spatial Lag ---
cat("Ajustando modelo Spatial Lag...\n")
lag <- lagsarlm(fmla, data = gdf, listw = lw)
summary_lag <- summary(lag)

# --- 8. Moran’s I en residuos OLS ---
cat("Calculando Moran's I en residuos OLS...\n")
moran_ols <- moran.test(residuals(ols), lw)

# --- 9. GWR ---
cat("Ajustando modelo GWR (esto puede tardar varios minutos)...\n")
gdf_sp <- as(gdf, "Spatial")
bw <- bw.gwr(fmla, data = gdf_sp, approach = "AICc", kernel = "bisquare", adaptive = TRUE)
gwr_mod <- gwr.basic(fmla, data = gdf_sp, bw = bw, kernel = "bisquare", adaptive = TRUE)

# --- 10. Exporta residuos y R2 local ---
cat("Exportando residuos y R2 local...\n")
gdf$residuals_ols <- residuals(ols)
gdf$residuals_lag <- residuals(lag)
gdf$localR2_gwr <- gwr_mod$SDF$localR2

# --- 11. HOTSPOTS TÉRMICOS Y CRUCE CON VULNERABILIDAD ---
cat("Identificando hotspots térmicos y cruzando con vulnerabilidad...\n")
umbral_hotspot <- quantile(gdf$Ta_max, 0.9, na.rm = TRUE)
gdf$hotspot_ter <- gdf$Ta_max >= umbral_hotspot

vuln_vars <- c(
  "pct_0a5", "pct_60plus", "pct_hli", "pct_afro", "pct_disc", "pct_inac", "pct_no_serv_med",
  "vul_PRO_OCUP_C", "vul_GRAPROES"
)

for (v in vuln_vars) {
  umbral_v <- quantile(gdf[[v]], 0.9, na.rm = TRUE)
  new_col <- paste0("hotspot_", v)
  gdf[[new_col]] <- gdf$hotspot_ter & (gdf[[v]] >= umbral_v)
}

# --- 12. TABLAS DESCRIPTIVAS ---
cat("Generando tablas descriptivas de doble hotspot...\n")
tabla_hotspots <- sapply(vuln_vars, function(v) {
  col <- paste0("hotspot_", v)
  sum(gdf[[col]], na.rm = TRUE)
})
tabla_prop <- sapply(vuln_vars, function(v) {
  col <- paste0("hotspot_", v)
  mean(gdf[[col]], na.rm = TRUE)
})
tabla_hotspots <- data.frame(Grupo = vuln_vars, Manzanas_doble_hotspot = tabla_hotspots, Prop_manzanas_doble_hotspot = tabla_prop)
print(tabla_hotspots)

# --- 13. Exportar resultados ---
cat("Exportando resultados en GPKG...\n")
out_gpkg <- "resultados_regresion_y_hotspots.gpkg"
tryCatch({
  st_write(gdf, out_gpkg, delete_layer = TRUE, quiet = TRUE)
}, error = function(e) {
  warning("❌ Error al guardar GPKG: ", e$message)
})

cat("Exportando sumarios de regresión a TXT...\n")
capture.output(summary_ols, file = "summary_ols.txt")
capture.output(summary_lag, file = "summary_spatial_lag.txt")
capture.output(moran_ols, file = "moran_ols.txt")
capture.output(summary(gwr_mod), file = "summary_gwr.txt")

# --- 14. Mapas en PNG, SVG (alta resolución, buenas leyendas) ---
cat("Generando mapas finales (PNG y SVG)...\n")
dir.create("figures_median_scale", showWarnings = FALSE)

# Mapas que puedes ajustar o replicar para cada resultado de interés:
tmap_mode("plot")
# a) Hotspots térmicos
m_hot <- tm_shape(gdf) +
  tm_fill("hotspot_ter", palette = c("white", "red"), title = "Hotspot térmico (Ta_max ≥ p90)", legend.format = list(fun = function(x) ifelse(x == 1, "Hotspot", "No hotspot"))) +
  tm_borders(col = "grey60") +
  tm_layout(title = "Hotspots térmicos CDMX", legend.outside = TRUE, legend.outside.position = "right", legend.title.size = 1.2, legend.text.size = 1, frame = FALSE)

tmap_save(m_hot, "figures_median_scale/mapa_hotspot_ter.png", width=3000, height=2200, dpi=320)
tmap_save(m_hot, "figures_median_scale/mapa_hotspot_ter.svg", width=16, height=10)

# b) R² local GWR
m_r2 <- tm_shape(gdf) +
  tm_fill("localR2_gwr", style = "quantile", n = 5, palette = "Blues", title = expression(R^2~local~"(GWR)")) +
  tm_borders(col = "grey60") +
  tm_layout(title = "R² local (GWR)", legend.outside = TRUE, legend.outside.position = "right", legend.title.size = 1.2, legend.text.size = 1, frame = FALSE)
tmap_save(m_r2, "figures_median_scale/mapa_localR2_gwr.png", width=3000, height=2200, dpi=320)
tmap_save(m_r2, "figures_median_scale/mapa_localR2_gwr.svg", width=16, height=10)

# c) Ejemplo: Hotspot doble para adultos mayores
m_vuln <- tm_shape(gdf) +
  tm_fill("hotspot_pct_60plus", palette = c("white", "purple"), title = "Hotspot térmico +\n% adultos mayores ≥ p90", legend.format = list(fun = function(x) ifelse(x == 1, "Doble hotspot", "No"))) +
  tm_borders(col = "grey60") +
  tm_layout(title = "Doble Hotspot: Calor + Adultos Mayores", legend.outside = TRUE, legend.outside.position = "right", legend.title.size = 1.2, legend.text.size = 1, frame = FALSE)
tmap_save(m_vuln, "figures_median_scale/mapa_doble_hotspot_60plus.png", width=3000, height=2200, dpi=320)
tmap_save(m_vuln, "figures_median_scale/mapa_doble_hotspot_60plus.svg", width=16, height=10)

cat("\n✅ Listo. Revisa la carpeta 'figures_median_scale/' para mapas PNG/SVG en alta resolución y leyendas claras.\n")
cat("Resultados tabulares y shapefile en 'resultados_regresion_y_hotspots.gpkg'.\n")
