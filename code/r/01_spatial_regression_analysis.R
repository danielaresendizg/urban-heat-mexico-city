# --- 1. Librerías ---
library(sf)
library(spdep)
library(spatialreg)
library(GWmodel)
library(dplyr)

# --- 2. Leer datos ---
ruta <- "~/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/manzanas_IVS_heat_20250707_sin_nulos.gpkg"
gdf <- st_read(ruta, quiet = TRUE)

# --- 3. Variables óptimas según lo discutido ---
vars <- c(
  "Ta_max",        # Dependiente
  "NDVI_mean",     # Control físico (vegetación)
  "pct_0a5", "pct_60plus", "pct_hli", "pct_afro", "pct_disc", "pct_inac", "pct_no_serv_med",
  "vul_PRO_OCUP_C", "vul_GRAPROES"  # Vulnerabilidad específica
)

# Chequeo de variables faltantes
faltantes <- setdiff(vars, names(gdf))
if(length(faltantes) > 0) warning("Variables faltantes en el shapefile: ", paste(faltantes, collapse = ", "))

# Selecciona solo las existentes y elimina NA
vars <- vars[vars %in% names(gdf)]
gdf <- gdf |> select(any_of(vars)) |> na.omit()

# --- 3b. Validar geometría y proyección ---
if(st_is_longlat(gdf)) stop("Transforma tu geometría a un CRS proyectado (en metros) antes del análisis espacial, por ejemplo:\n gdf <- st_transform(gdf, 32614)")
if(any(!st_is_valid(gdf))) gdf <- st_make_valid(gdf)

# --- 4. Matriz de pesos espaciales (KNN, k=8) ---
coords <- st_coordinates(st_centroid(gdf))
knn <- knearneigh(coords, k=8)
nb <- knn2nb(knn)
lw <- nb2listw(nb, style = "W")

# --- 5. Fórmula de regresión ---
fmla <- as.formula(
  paste("Ta_max ~", paste(vars[vars != "Ta_max" & vars != "geometry"], collapse = " + "))
)

# --- 6. OLS clásico ---
ols <- lm(fmla, data = gdf)
summary_ols <- summary(ols)

# --- 7. Spatial Lag ---
lag <- lagsarlm(fmla, data = gdf, listw = lw)
summary_lag <- summary(lag)

# --- 8. Moran’s I en residuos OLS ---
moran_ols <- moran.test(residuals(ols), lw)

# --- 9. GWR (Geographically Weighted Regression) ---
# GWmodel requiere objetos Spatial
gdf_sp <- as(gdf, "Spatial")
bw <- bw.gwr(fmla, data = gdf_sp, approach = "AICc", kernel = "bisquare", adaptive = TRUE)
gwr_mod <- gwr.basic(fmla, data = gdf_sp, bw = bw, kernel = "bisquare", adaptive = TRUE)

# --- 10. Exporta residuos y R2 local ---
gdf$residuals_ols <- residuals(ols)
gdf$residuals_lag <- residuals(lag)
gdf$localR2_gwr <- gwr_mod$SDF$localR2

# --- 11. Guarda los resultados en GPKG ---
out_gpkg <- "figures_median_scale/resultados_regresion_lit.gpkg"
if(!dir.exists("figures_median_scale")) dir.create("figures_median_scale")
st_write(gdf, out_gpkg, delete_layer = TRUE, quiet = TRUE)

# --- 12. Guardar resúmenes en txt ---
capture.output(summary_ols, file = "figures_median_scale/summary_ols.txt")
capture.output(summary_lag, file = "figures_median_scale/summary_spatial_lag.txt")
capture.output(moran_ols, file = "figures_median_scale/moran_ols.txt")
capture.output(summary(gwr_mod), file = "figures_median_scale/summary_gwr.txt")

# --- 13. Mapas en PNG y SVG para edición ---
# R² local GWR
png("figures_median_scale/mapa_localR2_gwr.png", width=1200, height=1000)
plot(gdf["localR2_gwr"], main="R² local (GWR) para Ta_max", key.pos = 1, reset=FALSE)
dev.off()
svg("figures_median_scale/mapa_localR2_gwr.svg", width=14, height=10)
plot(gdf["localR2_gwr"], main="R² local (GWR) para Ta_max", key.pos = 1, reset=FALSE)
dev.off()

# Residuos Spatial Lag
png("figures_median_scale/mapa_residuos_lag.png", width=1200, height=1000)
plot(gdf["residuals_lag"], main="Residuos Spatial Lag", key.pos = 1, reset=FALSE)
dev.off()
svg("figures_median_scale/mapa_residuos_lag.svg", width=14, height=10)
plot(gdf["residuals_lag"], main="Residuos Spatial Lag", key.pos = 1, reset=FALSE)
dev.off()

# Residuos OLS
png("figures_median_scale/mapa_residuos_ols.png", width=1200, height=1000)
plot(gdf["residuals_ols"], main="Residuos OLS", key.pos = 1, reset=FALSE)
dev.off()
svg("figures_median_scale/mapa_residuos_ols.svg", width=14, height=10)
plot(gdf["residuals_ols"], main="Residuos OLS", key.pos = 1, reset=FALSE)
dev.off()

cat("\n🚀 Listo: revisa los resultados y mapas en figures_median_scale/\n")

