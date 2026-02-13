# 1. Revisar si el CSV de hotspots existe y tiene la columna CVEGEO
csv_hotspot="/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/manzana_con_hotspot.csv"
if [ -f "$csv_hotspot" ]; then
    echo "✅ CSV encontrado: $csv_hotspot"
    head -n 2 "$csv_hotspot" | cut -d',' -f1-20
    grep -m 1 "CVEGEO" "$csv_hotspot" >/dev/null && echo "✅ Contiene columna CVEGEO" || echo "❌ No tiene CVEGEO"
else
    echo "❌ CSV no encontrado"
fi

# 2. Revisar si el GPKG existe
gpkg_manzanas="/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/GWR/GWR_merge/manzanas_master_con_GWR_spacematrix_v3lite.gpkg"
if [ -f "$gpkg_manzanas" ]; then
    echo "✅ GPKG encontrado: $gpkg_manzanas"
else
    echo "❌ GPKG no encontrado"
fi

# 3. Listar capas dentro del GPKG (requiere ogrinfo de GDAL)
if command -v ogrinfo >/dev/null; then
    ogrinfo -q "$gpkg_manzanas" | grep "manzanas"
else
    echo "⚠️ No tienes ogrinfo instalado (instala GDAL si quieres listar capas)"
fi
