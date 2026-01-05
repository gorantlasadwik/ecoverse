import pandas as pd
import numpy as np

print("=== CREATING CORRECTED EXTENDED DATASET WITH CROP NAMES ===")

# Load all datasets
df_crop_yield = pd.read_csv('dataset 3/crop_yield.csv')
df_mapping = pd.read_csv('crop_mapping.csv')
df_sensors = pd.read_csv('dataset 5/Dataset_sensors.csv')
df_weather = pd.read_csv('dataset 2/Farm_Weather_Data.csv')

print(f"Starting with {len(df_crop_yield):,} records from crop yield data")

# Set random seed for reproducibility
np.random.seed(42)

# ============================================
# CREATE EXTENDED FEATURES (NO DATA LOSS)
# ============================================
df_extended = df_crop_yield.copy()

# Default sensor ranges (since Dataset 5 might have issues)
sensor_ranges = {
    'soil_moisture': (40, 70),
    'soil_temperature': (18, 32), 
    'weather_temperature': (15, 40),
    'weather_humidity': (35, 95),
    'solar_radiation': (20, 100)
}

print(f"\n=== CREATING SENSOR FEATURES ===")

# 1. SOIL_MOISTURE - based on fertilizer usage and season
df_extended['fertilizer_normalized'] = (df_extended['fertilizer'] - df_extended['fertilizer'].min()) / (df_extended['fertilizer'].max() - df_extended['fertilizer'].min())

season_soil_moisture = {
    'Kharif': 55,      # Monsoon - high moisture
    'Rabi': 35,        # Winter - moderate  
    'Summer': 25,      # Summer - low
    'Autumn': 45,      # Post-monsoon - moderate-high
    'Whole Year': 40   # Average
}

df_extended['soil_moisture'] = df_extended['season'].map(season_soil_moisture).fillna(40)
df_extended['soil_moisture'] *= (0.7 + 0.6 * (1 - df_extended['fertilizer_normalized']))
df_extended['soil_moisture'] += np.random.normal(0, 3, len(df_extended))
df_extended['soil_moisture'] = df_extended['soil_moisture'].clip(*sensor_ranges['soil_moisture'])

# 2. SOIL_TEMPERATURE - correlated with air temperature but lower
df_extended['soil_temperature'] = df_extended['soil_moisture'] * 0.3 + 18
df_extended['soil_temperature'] += (df_extended['year'] - 1997) * 0.015
df_extended['soil_temperature'] += np.random.normal(0, 1.5, len(df_extended))
df_extended['soil_temperature'] = df_extended['soil_temperature'].clip(*sensor_ranges['soil_temperature'])

# 3. WEATHER_TEMPERATURE - seasonal patterns
season_weather_temp = {
    'Kharif': 28, 'Rabi': 20, 'Summer': 35, 'Autumn': 26, 'Whole Year': 27
}

df_extended['weather_temperature'] = df_extended['season'].map(season_weather_temp).fillna(27)
df_extended['weather_temperature'] += (df_extended['year'] - 1997) * 0.02
df_extended['weather_temperature'] += np.random.normal(0, 2, len(df_extended))
df_extended['weather_temperature'] = df_extended['weather_temperature'].clip(*sensor_ranges['weather_temperature'])

# 4. WEATHER_HUMIDITY - seasonal patterns
season_humidity = {
    'Kharif': 75, 'Rabi': 55, 'Summer': 45, 'Autumn': 70, 'Whole Year': 62
}

df_extended['weather_humidity'] = df_extended['season'].map(season_humidity).fillna(62)
df_extended['weather_humidity'] += np.random.normal(0, 5, len(df_extended))
df_extended['weather_humidity'] = df_extended['weather_humidity'].clip(*sensor_ranges['weather_humidity'])

# 5. SOLAR_RADIATION - seasonal and humidity dependent
season_solar = {
    'Kharif': 40, 'Rabi': 65, 'Summer': 85, 'Autumn': 50, 'Whole Year': 60
}

df_extended['solar_radiation'] = df_extended['season'].map(season_solar).fillna(60)
df_extended['solar_radiation'] *= (1.3 - df_extended['weather_humidity'] / 100)
df_extended['solar_radiation'] += np.random.normal(0, 8, len(df_extended))
df_extended['solar_radiation'] = df_extended['solar_radiation'].clip(*sensor_ranges['solar_radiation'])

print(f"✓ Created sensor features for {len(df_extended):,} records")

# ============================================
# ADD WEATHER DATA FEATURES
# ============================================
print(f"\n=== ADDING WEATHER FEATURES ===")

# Create synthetic dates for joining
df_extended['synthetic_date'] = pd.to_datetime(df_extended['year'].astype(str) + '-01-01') + \
                               pd.to_timedelta(np.random.randint(0, 365, len(df_extended)), unit='D')

# Parse weather data
df_weather['Date'] = pd.to_datetime(df_weather['Date'])
weather_daily = df_weather.groupby(df_weather['Date'].dt.date).agg({
    'MaxT': 'mean', 'MinT': 'mean', 'Precipitation': 'sum'
}).reset_index()

# Merge weather data
df_extended['Date'] = df_extended['synthetic_date'].dt.date
df_extended = df_extended.merge(weather_daily, on='Date', how='left')

# Fill missing weather with seasonal defaults
weather_defaults = {
    'MaxT': {'Kharif': 32, 'Rabi': 25, 'Summer': 38, 'Autumn': 30, 'Whole Year': 31},
    'MinT': {'Kharif': 24, 'Rabi': 15, 'Summer': 28, 'Autumn': 22, 'Whole Year': 22},
    'Precipitation': {'Kharif': 8, 'Rabi': 0.5, 'Summer': 0.2, 'Autumn': 3, 'Whole Year': 3}
}

for col, season_map in weather_defaults.items():
    df_extended[col] = df_extended[col].fillna(df_extended['season'].map(season_map))

# Add climate trends and variations
df_extended['MaxT'] += (df_extended['year'] - 1997) * 0.025 + np.random.normal(0, 2, len(df_extended))
df_extended['MinT'] += (df_extended['year'] - 1997) * 0.02 + np.random.normal(0, 1.5, len(df_extended))
df_extended['Precipitation'] += np.random.exponential(2, len(df_extended))

# Clip to reasonable ranges
df_extended['MaxT'] = df_extended['MaxT'].clip(15, 45)
df_extended['MinT'] = df_extended['MinT'].clip(5, 35)
df_extended['Precipitation'] = df_extended['Precipitation'].clip(0, 50)

print(f"✓ Added weather features for {len(df_extended):,} records")

# ============================================
# ADD MOISTURE TREND
# ============================================
print(f"\n=== CALCULATING MOISTURE TREND ===")

# Create synthetic moisture trends based on season and crop patterns
seasonal_trend_base = {
    'Kharif': 0.5,      # Increasing during monsoon
    'Rabi': -0.3,       # Decreasing in winter  
    'Summer': -1.5,     # Rapidly decreasing in summer
    'Autumn': 0.8,      # Increasing post-monsoon
    'Whole Year': 0.0   # Neutral
}

df_extended['Moisture_Trend'] = df_extended['season'].map(seasonal_trend_base).fillna(0)
df_extended['Moisture_Trend'] += np.random.normal(0, 1.2, len(df_extended))
df_extended['Moisture_Trend'] = df_extended['Moisture_Trend'].clip(-5, 5)

print(f"✓ Added moisture trend for {len(df_extended):,} records")

# ============================================
# PRESERVE CROP NAMES (NO ENCODING)
# ============================================
print(f"\n=== PRESERVING CROP NAMES ===")

# Clean crop names but keep as text
df_extended['Crop'] = df_extended['crop'].str.title().str.strip()

print(f"✓ Crop names preserved: {len(df_extended['Crop'].unique())} unique crops")

# ============================================
# CREATE FINAL EXTENDED DATASET WITH CROP NAMES
# ============================================
print(f"\n=== CREATING FINAL DATASET ===")

# Select final columns (crop names, not IDs)
final_columns = [
    'soil_moisture',
    'soil_temperature', 
    'weather_temperature',
    'weather_humidity',
    'solar_radiation',
    'MaxT',
    'MinT', 
    'Precipitation',
    'Moisture_Trend',
    'Crop'  # Crop names, not IDs
]

df_final = df_extended[final_columns].copy()

# Ensure numeric types (except Crop which stays as string)
for col in final_columns[:-1]:
    df_final[col] = pd.to_numeric(df_final[col], errors='coerce')

# Remove any rows with missing values (should be minimal)
initial_count = len(df_final)
df_final = df_final.dropna()
final_count = len(df_final)

print(f"✓ Final dataset: {final_count:,} records")
if initial_count != final_count:
    print(f"  Removed {initial_count - final_count} records with missing values")

# ============================================
# SAVE BOTH VERSIONS
# ============================================
print(f"\n=== SAVING DATASETS ===")

# Save version with crop names
df_final.to_csv('decision_base_extended_with_names.csv', index=False)
print(f"✓ Saved decision_base_extended_with_names.csv ({len(df_final):,} records)")

# Create version with crop IDs for comparison
df_final_ids = df_final.copy()

# Create crop name to ID mapping
crop_to_id = dict(zip(df_mapping['Crop_Name'], df_mapping['Encoded_Value']))

# Handle crop name variations
crop_name_fixes = {
    'Cotton(Lint)': 'Cotton(lint)', 'Black Pepper': 'Black pepper', 'Dry Chillies': 'Dry chillies',
    'Coconut': 'Coconut ', 'Castor Seed': 'Castor seed', 'Sweet Potato': 'Sweet potato',
    'Small Millets': 'Small millets', 'Niger Seed': 'Niger seed', 'Horse-Gram': 'Horse-gram',
    'Guar Seed': 'Guar seed', 'Oilseeds Total': 'Oilseeds total', 'Other  Rabi Pulses': 'Other  Rabi pulses',
    'Other Kharif Pulses': 'Other Kharif pulses', 'Other Oilseeds': 'other oilseeds',
    'Peas & Beans (Pulses)': 'Peas & beans (Pulses)'
}

# Apply name fixes
for wrong, correct in crop_name_fixes.items():
    df_final_ids.loc[df_final_ids['Crop'] == wrong, 'Crop'] = correct

# Map to IDs
df_final_ids['Crop_ID'] = df_final_ids['Crop'].map(crop_to_id)

# Handle any unmapped crops
unmapped = df_final_ids['Crop_ID'].isna()
if unmapped.sum() > 0:
    print(f"  Found {unmapped.sum()} unmapped crops, assigning new IDs...")
    max_id = max(crop_to_id.values())
    unmapped_crops = df_final_ids[unmapped]['Crop'].unique()
    for i, crop in enumerate(unmapped_crops):
        new_id = max_id + i + 1
        df_final_ids.loc[df_final_ids['Crop'] == crop, 'Crop_ID'] = new_id

df_final_ids['Crop'] = df_final_ids['Crop_ID'].astype(int)
df_final_ids = df_final_ids.drop('Crop_ID', axis=1)

# Save version with crop IDs
df_final_ids.to_csv('decision_base_extended_with_ids.csv', index=False)
print(f"✓ Saved decision_base_extended_with_ids.csv ({len(df_final_ids):,} records)")

# ============================================
# SUMMARY
# ============================================
print(f"\n=== SUMMARY ===")
print(f"✅ Original records: {len(df_crop_yield):,}")
print(f"✅ Final records (names): {len(df_final):,}")
print(f"✅ Final records (IDs): {len(df_final_ids):,}")
print(f"✅ Data preservation: {len(df_final)/len(df_crop_yield)*100:.1f}%")

print(f"\nFeatures created:")
for col in final_columns:
    print(f"  ✓ {col}")

print(f"\nTop crops:")
print(df_final['Crop'].value_counts().head(5))

print(f"\nSample data (with crop names):")
print(df_final.head())

print(f"\n✅ BOTH VERSIONS CREATED SUCCESSFULLY!")
print(f"📁 decision_base_extended_with_names.csv - Contains crop names")
print(f"📁 decision_base_extended_with_ids.csv - Contains crop IDs")