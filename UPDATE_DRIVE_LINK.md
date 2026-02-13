# How to Update Google Drive Link

## Current Status

✅ Data copied to Google Drive: `My Drive/03_Consulting/dissertation_data/` (2.8 GB)
⚠️ **Action needed:** Replace `YOUR_FOLDER_ID_HERE` with actual folder ID

---

## Steps to Get the Folder ID

### 1. Share the folder publicly

1. Go to: https://drive.google.com
2. Navigate to: `My Drive` → `03_Consulting` → `dissertation_data`
3. Right-click on the `dissertation_data` folder
4. Click **"Share"**
5. Click **"Change to anyone with the link"**
6. Set permissions to **"Viewer"** (read-only)
7. Click **"Copy link"**

### 2. Extract the Folder ID

The link will look like this:
```
https://drive.google.com/drive/folders/1a2B3c4D5e6F7g8H9i0JkLmN/view?usp=sharing
```

The Folder ID is the part between `/folders/` and `/view`:
```
1a2B3c4D5e6F7g8H9i0JkLmN
```

### 3. Update the repository files

Run this command, replacing `PASTE_YOUR_FOLDER_ID` with the actual ID:

```bash
cd ~/GitHub/urban-heat-mexico-city

# Replace placeholder with actual folder ID
find . -type f \( -name "*.md" -o -name "*.txt" \) -exec sed -i '' 's/YOUR_FOLDER_ID_HERE/PASTE_YOUR_FOLDER_ID/g' {} +

# Verify changes
grep -r "drive.google.com" . --include="*.md" | grep -v ".git"
```

---

## Files that need updating

The following files contain `YOUR_FOLDER_ID_HERE`:

1. `README.md` (line 181)
2. `DATA_SOURCES.md` (multiple lines)
3. `code/python/preprocessing/README.md` (line 80)
4. `data/README.md` (line 18)

---

## Alternative: Manual Update

If you prefer to update manually:

1. Open each file listed above
2. Search for `YOUR_FOLDER_ID_HERE`
3. Replace with your actual folder ID
4. Save

---

## Verify the Link Works

After updating, test the link in an incognito window:
```
https://drive.google.com/drive/folders/YOUR_ACTUAL_ID?usp=sharing
```

You should see:
- ✅ 8 folders (manzanas, street_network, gwr, thermal_rasters, redmet, buildings, boundaries, environment)
- ✅ 1 file (README.md)
- ✅ Anyone can view (no sign-in required)

---

## After Verification

1. Delete this file: `UPDATE_DRIVE_LINK.md`
2. Commit changes:
   ```bash
   cd ~/GitHub/urban-heat-mexico-city
   git add -A
   git commit -m "Add Google Drive link for dissertation data (2.8 GB)"
   git push
   ```

---

## Quick Command Reference

```bash
# After getting folder ID, run this ONE command:
cd ~/GitHub/urban-heat-mexico-city && \
find . -type f -name "*.md" -exec sed -i '' 's/YOUR_FOLDER_ID_HERE/YOUR_ACTUAL_FOLDER_ID_HERE/g' {} + && \
git add -A && \
git status
```

Replace `YOUR_ACTUAL_FOLDER_ID_HERE` with the ID you copied from Google Drive.
