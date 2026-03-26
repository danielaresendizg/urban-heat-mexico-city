#!/usr/bin/env bash
set -euo pipefail

# Sync atlas layers from Google Drive (updated pipeline outputs)
# Output files are written to docs/data for docs/atlas_cdmx.html

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/docs/data"
TMP_DIR="${TMPDIR:-/tmp}/uh_drive_sync"

# Geometry optimization knobs (keep all layers/fields, only simplify shape detail)
# Set any SIMPLIFY_* to 0 to disable simplification for that layer.
SIMPLIFY_MANZANAS="${SIMPLIFY_MANZANAS:-0.00008}"
SIMPLIFY_NETWORK="${SIMPLIFY_NETWORK:-0.00030}"
SIMPLIFY_PRIORITY="${SIMPLIFY_PRIORITY:-0.00008}"
COORD_PRECISION="${COORD_PRECISION:-4}"
BUILD_INLINE_JS="${BUILD_INLINE_JS:-1}"

mkdir -p "$OUT_DIR" "$TMP_DIR"

# Drive file IDs (current updated repo data)
MANZANAS_GPKG_ID="1ymjqskEjQcfPLRu0XbbgTecbEqDW43Py"          # step_5_hotspots
SEGMENTS_GPKG_ID="1dhvBQwCvHDEQM6ahS-pD6o3MBCpFIMBW"          # step_7_space_syntax
PRIORITY_GPKG_ID="1Sq2JjJieVVFDqtlvKMazaw8C_AhaRj27"          # step_8_prioritization

MANZANAS_GPKG="$TMP_DIR/manzanas.gpkg"
SEGMENTS_GPKG="$TMP_DIR/segments.gpkg"
PRIORITY_GPKG="$TMP_DIR/priority.gpkg"

curl -L "https://drive.usercontent.google.com/download?id=${MANZANAS_GPKG_ID}&export=download&confirm=t" -o "$MANZANAS_GPKG"
curl -L "https://drive.usercontent.google.com/download?id=${SEGMENTS_GPKG_ID}&export=download&confirm=t" -o "$SEGMENTS_GPKG"
curl -L "https://drive.usercontent.google.com/download?id=${PRIORITY_GPKG_ID}&export=download&confirm=t" -o "$PRIORITY_GPKG"

MANZANAS_TMP="$TMP_DIR/manzanas.geojson"
NETWORK_TMP="$TMP_DIR/network.geojson"
PRIORITY_TMP="$TMP_DIR/priority.geojson"

# Manzanas: all fields required by atlas layers (geometry simplification configurable)
ogr2ogr -f GeoJSON \
  -dialect SQLITE \
  -sql "SELECT \
    CVEGEO, NOM_MUN, \
    Ta_mean, LST_mean, UHI_mean, NDVI_mean, Albedo_mean, NDBI_mean, \
    pct_65plus, pct_6a14, pct_0a5, pct_with_disc, pct_pop_sin_auto, \
    pct_no_serv_med, pct_inac, pct_desocup, pct_no_school, pct_elementary_edu, \
    pct_ethnic_ind, pct_ethnic_afro, rel_dependencia_0_14, \
    peligro_cat, is_hot_26, is_hot_28, hot26_count_social, hot28_count_social, \
    hot26_pct_65plus, hot26_pct_with_disc, hot26_pct_pop_sin_auto, \
    hot26_pct_no_serv_med, hot26_pct_inac, hot26_pct_6a14, hot26_pct_elementary_edu, \
    typology_sm_final, FSI, GSI, OSR, L_equiv, \
    geom \
    FROM manzanas_typology_SM_v2" \
  -t_srs EPSG:4326 \
  -simplify "$SIMPLIFY_MANZANAS" \
  -lco RFC7946=YES -lco COORDINATE_PRECISION="$COORD_PRECISION" \
  "$MANZANAS_TMP" "$MANZANAS_GPKG"

# Network: all fields required by atlas layers (geometry simplification configurable)
ogr2ogr -f GeoJSON \
  -dialect SQLITE \
  -sql "SELECT \
    CAST(NAINr500m AS REAL) AS NAINr500m, \
    CAST(NAINr1500m AS REAL) AS NAINr1500m, \
    CAST(NAINr5000m AS REAL) AS NAINr5000m, \
    CAST(NACHr500m AS REAL) AS NACHr500m, \
    CAST(NACHr1500m AS REAL) AS NACHr1500m, \
    CAST(NACHr5000m AS REAL) AS NACHr5000m, \
    CAST(Ta_mean AS REAL) AS Ta_mean, \
    CAST(UHI_mean AS REAL) AS UHI_mean, \
    CAST(NDVI_mean AS REAL) AS NDVI_mean, \
    peligro_cat, \
    geom \
    FROM segments" \
  -t_srs EPSG:4326 \
  -simplify "$SIMPLIFY_NETWORK" \
  -lco RFC7946=YES -lco COORDINATE_PRECISION="$COORD_PRECISION" \
  "$NETWORK_TMP" "$SEGMENTS_GPKG"

# Priority: include TOP and ZONES with full attributes + ltype tag
ogr2ogr -f GeoJSON \
  -dialect SQLITE \
  -sql "SELECT *, 'top' AS ltype FROM syntax_only_TOP_20250816_0042" \
  -t_srs EPSG:4326 \
  -simplify "$SIMPLIFY_PRIORITY" \
  -lco RFC7946=YES -lco COORDINATE_PRECISION="$COORD_PRECISION" \
  "$PRIORITY_TMP" "$PRIORITY_GPKG"

ogr2ogr -f GeoJSON \
  -append -addfields \
  -dialect SQLITE \
  -sql "SELECT *, 'zone' AS ltype FROM syntax_only_ZONES_20250816_0042" \
  -t_srs EPSG:4326 \
  -simplify "$SIMPLIFY_PRIORITY" \
  -lco RFC7946=YES -lco COORDINATE_PRECISION="$COORD_PRECISION" \
  "$PRIORITY_TMP" "$PRIORITY_GPKG"

mv "$MANZANAS_TMP" "$OUT_DIR/manzanas.geojson"
mv "$NETWORK_TMP" "$OUT_DIR/network.geojson"
mv "$PRIORITY_TMP" "$OUT_DIR/priority.geojson"

# Build inline JS bundles (needed only when opening HTML via file://)
if [[ "$BUILD_INLINE_JS" == "1" ]]; then
  for n in manzanas network priority; do
    printf "window.ATLAS_INLINE_SOURCES = window.ATLAS_INLINE_SOURCES || {};\n" > "$OUT_DIR/${n}.inline.js"
    printf "window.ATLAS_INLINE_SOURCES['%s'] =\n" "$n" >> "$OUT_DIR/${n}.inline.js"
    cat "$OUT_DIR/${n}.geojson" >> "$OUT_DIR/${n}.inline.js"
    printf ";\n" >> "$OUT_DIR/${n}.inline.js"
  done
fi

ls -lh "$OUT_DIR"/*.geojson
