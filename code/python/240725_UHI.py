import pandas as pd

# Ruta de tu archivo
file_path = "/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation/01_data/01_Manzana/manzanas_IVS_20250724.csv"
df = pd.read_csv(file_path)

# Asegúrate de que Ta_mean sea numérico
df['Ta_mean'] = pd.to_numeric(df['Ta_mean'], errors='coerce')

# Calcula la media
ta_mean_city = df['Ta_mean'].mean()

print(f"Media Ta_mean en todas las manzanas: {ta_mean_city:.2f} °C")

# Calcula UHI para cada manzana
df['UHI'] = df['Ta_mean'] - ta_mean_city

# Estadísticas de UHI
print(df['UHI'].describe())
