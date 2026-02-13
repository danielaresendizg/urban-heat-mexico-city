# Google Drive Data Sharing Setup

This guide explains how to share the RedMet data folder on Google Drive and update the repository with the public link.

## Current Status

✅ RedMet data copied to: `My Drive/03_Consulting/dissertation_data/redmet/`

## Steps to Create Public Share Link

### 1. Open Google Drive in your browser
Navigate to: https://drive.google.com

### 2. Locate the redmet folder
Go to: `My Drive` → `03_Consulting` → `dissertation_data` → `redmet`

### 3. Share the folder
1. **Right-click** on the `redmet` folder
2. Select **"Share"** or click the share icon
3. Click **"Change to anyone with the link"**
4. Set permissions to **"Viewer"** (read-only)
5. Click **"Copy link"**

### 4. Update the repository README

Copy the Google Drive link and update these files:

**File: `data/README.md`**

Find this line:
```markdown
**Access:** [Google Drive Link - To be added]
```

Replace with:
```markdown
**Access:** [RedMet Data Folder](YOUR_GOOGLE_DRIVE_LINK_HERE)
```

### 5. Commit the changes

```bash
cd ~/GitHub/urban-heat-mexico-city
git add data/README.md
git commit -m "Add Google Drive link for RedMet historical data"
git push
```

## Folder Structure on Google Drive

```
redmet/
├── Estaciones_historico_14-24/    # Historical XLS files (2014-2024)
│   ├── 14REDMET/
│   │   ├── 2014TMP.xls
│   │   └── 2014RH.xls
│   ├── 15REDMET/
│   ├── ... (16-23)
│   └── 24REDMET/
│       ├── 2024TMP.xls
│       └── 2024RH.xls
│
├── procesados/                     # Processed outputs
│   ├── verano_14-24_long.parquet
│   ├── redmet_diurnal.csv
│   └── redmet_nocturnal.csv
│
├── scripts/
│   └── process_redmet.py
│
├── estaciones_operacion_CDMX.csv
├── estaciones_operacion_CDMX.gpkg
└── estaciones_operacion_CDMX_final.csv
```

## Alternative: Download Instructions for Users

If you prefer not to share publicly, you can provide download instructions instead:

**Update `data/README.md` with:**

```markdown
### RedMet Historical Data (2014-2024)

**Access:** Contact author or download from SEDEMA-CDMX:
- Website: https://www.aire.cdmx.gob.mx/
- Data Portal: http://www.aire.cdmx.gob.mx/default.php?opc=%27aKBhnmI=%27

**Required files:**
- Historical temperature and humidity data (2014-2024)
- Station metadata and locations
```

## File Size Reference

Total folder size: ~48 KB (very small, easily shareable)

## Privacy Note

The RedMet data is public meteorological data from SEDEMA-CDMX. Sharing it publicly via Google Drive link is appropriate and does not contain sensitive information.
