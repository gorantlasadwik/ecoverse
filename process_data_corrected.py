import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================
# MEMBER A - Base Dataset & Weather Integration
# CORRECTED VERSION - Using Dataset 3 (19K rows)
# ============================================

print("Loading datasets...")

try:
    # Dataset 3: Crop Yield Data (19K rows) - PRIMARY SOURCE
    df_crop_yield = pd.read_csv(r'c:\Users\sadwi\OneDrive\Desktop\Data\dataset 3\crop_yield.csv')
    print(f"✓ Crop Yield Data loaded: {df_crop_yield.shape}")
    
    # Dataset 4: Smart Farming IoT Data (supplementary)
    df_iot = pd.read_csv(r'c:\Users\sadwi\OneDrive\Desktop\Data\dataset 4\Smart_Farming_Crop_Yield_2024.csv')
    print(f"✓ Smart Farming IoT Data loaded: {df_iot.shape}")
    
    # Dataset 5: Additional Sensor Data
    df_sensors = pd.read_csv(r'c:\Users\sadwi\OneDrive\Desktop\Data\dataset 5\Dataset_sensors.csv')
    print(f"✓ Sensor Data loaded: {df_sensors.shape}")
    
    # Dataset 2: Farm Weather Data
    df_weather = pd.read_csv(r'c:\Users\sadwi\OneDrive\Desktop\Data\dataset 2\Farm_Weather_Data.csv')
    print(f"✓ Weather Data loaded: {df_weather.shape}")
    
except Exception as e:
    print(f"Error loading files: {e}")
    exit()

# ============================================
# STEP 1: Create Base Dataset from Crop Yield Data (19K rows)
# ============================================
print("\n" + "="*50)
print("STEP 1: Create Base Dataset from Crop Yield Data")
print("="*50)

# Dataset 3 has: crop, year, season, state, area, production, fertilizer, pesticide, yield
# We need to create: Soil_Moisture, Temperature, Humidity, Rainfall, Crop

# Start with crop data as base
df_base = df_crop_yield.copy()

# Map from existing data and supplement with IoT data patterns
print(f"Original dataset: {df_base.shape}")

# Create Soil_Moisture based on yield and fertilizer usage (synthetic but logical)
# Higher fertilizer use typically indicates lower natural soil fertility
df_base['fertilizer_normalized'] = (df_base['fertilizer'] - df_base['fertilizer'].min()) / (df_base['fertilizer'].max() - df_base['fertilizer'].min())
df_base['Soil_Moisture'] = 15 + (1 - df_base['fertilizer_normalized']) * 30  # Range 15-45%

# Use IoT data patterns to create realistic variations
iot_soil_stats = df_iot['soil_moisture_%'].describe()
soil_std = iot_soil_stats['std']

# Add realistic noise based on IoT patterns
np.random.seed(42)  # For reproducibility
df_base['Soil_Moisture'] += np.random.normal(0, soil_std/3, len(df_base))
df_base['Soil_Moisture'] = df_base['Soil_Moisture'].clip(10, 50)  # Reasonable range

# Create Temperature based on year and season
season_temp_map = {
    'Kharif': 28,      # Monsoon season - warm
    'Rabi': 22,        # Winter season - cool  
    'Summer': 32,      # Summer season - hot
    'Autumn': 26,      # Post-monsoon - moderate
    'Whole Year': 26   # Average
}

df_base['Temperature'] = df_base['season'].map(season_temp_map).fillna(26)

# Add year-based temperature trend (climate change)
df_base['Temperature'] += (df_base['year'] - 1997) * 0.02  # 0.02°C per year

# Add random variation based on IoT data
iot_temp_stats = df_iot['temperature_C'].describe()
temp_std = iot_temp_stats['std']
df_base['Temperature'] += np.random.normal(0, temp_std/2, len(df_base))
df_base['Temperature'] = df_base['Temperature'].clip(10, 40)

# Create Humidity based on season and region patterns
season_humidity_map = {
    'Kharif': 75,      # Monsoon - high humidity
    'Rabi': 60,        # Winter - moderate
    'Summer': 45,      # Summer - low
    'Autumn': 68,      # Post-monsoon - high
    'Whole Year': 65   # Average
}

df_base['Humidity'] = df_base['season'].map(season_humidity_map).fillna(65)

# Add variation
iot_humidity_stats = df_iot['humidity_%'].describe()
humidity_std = iot_humidity_stats['std']
df_base['Humidity'] += np.random.normal(0, humidity_std/2, len(df_base))
df_base['Humidity'] = df_base['Humidity'].clip(30, 95)

# Create Rainfall based on yield and season (higher yield often correlates with good rainfall)
df_base['yield_normalized'] = (df_base['yield'] - df_base['yield'].min()) / (df_base['yield'].max() - df_base['yield'].min())

season_rainfall_base = {
    'Kharif': 150,     # Monsoon - high rainfall
    'Rabi': 20,        # Winter - low rainfall
    'Summer': 10,      # Summer - very low
    'Autumn': 80,      # Post-monsoon - moderate
    'Whole Year': 100  # Average
}

df_base['Rainfall'] = df_base['season'].map(season_rainfall_base).fillna(100)
df_base['Rainfall'] *= (0.5 + df_base['yield_normalized'])  # Yield correlation

# Add variation
iot_rain_stats = df_iot['rainfall_mm'].describe()
rain_std = iot_rain_stats['std']
df_base['Rainfall'] += np.random.normal(0, rain_std/2, len(df_base))
df_base['Rainfall'] = df_base['Rainfall'].clip(0, 400)

# Standardize crop names
df_base['Crop'] = df_base['crop'].str.title().str.strip()

print(f"✓ Base table created: {df_base.shape}")
print(f"Unique crops: {sorted(df_base['Crop'].unique())}")

# ============================================
# STEP 2: Integrate Additional Sensor Data (Dataset 5)
# ============================================
print("\n" + "="*50)
print("STEP 2: Integrate Additional Sensor Data")
print("="*50)

# Process Dataset 5 for moisture trends
df_sensors_clean = df_sensors.copy()
df_sensors_clean = df_sensors_clean[df_sensors_clean['soil_moisture'].notna()]

# Convert to numeric and calculate trends
df_sensors_clean['soil_moisture_norm'] = pd.to_numeric(df_sensors_clean['soil_moisture'], errors='coerce')
df_sensors_clean = df_sensors_clean.dropna(subset=['soil_moisture_norm'])

# Calculate moisture trend
window_size = 5
df_sensors_clean['moisture_diff'] = df_sensors_clean['soil_moisture_norm'].diff()
df_sensors_clean['Moisture_Trend_raw'] = df_sensors_clean['soil_moisture_norm'].pct_change() * 100
df_sensors_clean['Moisture_Trend'] = df_sensors_clean['Moisture_Trend_raw'].rolling(
    window=window_size, min_periods=1
).mean().fillna(0)

print(f"✓ Moisture trend calculated from {len(df_sensors_clean)} sensor readings")

# Distribute moisture trends across the large dataset
moisture_trends = df_sensors_clean['Moisture_Trend'].fillna(0).values
if len(moisture_trends) > 0:
    # Create repeating pattern for the large dataset
    trend_cycles = (len(df_base) // len(moisture_trends)) + 1
    trend_array = np.tile(moisture_trends, trend_cycles)[:len(df_base)]
    df_base['Moisture_Trend'] = trend_array
else:
    df_base['Moisture_Trend'] = 0.0

print(f"✓ Moisture trend added to {len(df_base)} records")
print(f"Moisture Trend stats: min={df_base['Moisture_Trend'].min():.3f}, max={df_base['Moisture_Trend'].max():.3f}")

# ============================================
# STEP 3: Merge Weather Data (Dataset 2)
# ============================================
print("\n" + "="*50)
print("STEP 3: Merge Weather Data")
print("="*50)

# Create synthetic dates for crop data (spread across years)
df_base['synthetic_date'] = pd.to_datetime(df_base['year'].astype(str) + '-01-01') + \
                           pd.to_timedelta(np.random.randint(0, 365, len(df_base)), unit='D')

# Parse weather data
df_weather['Date'] = pd.to_datetime(df_weather['Date'])
df_weather['Date_only'] = df_weather['Date'].dt.date

# Create weather aggregates by date
df_weather_agg = df_weather.groupby('Date_only').agg({
    'MaxT': 'mean',
    'MinT': 'mean', 
    'Humidity ': 'mean',
    'Precipitation': 'sum'
}).reset_index()

df_weather_agg.columns = ['Date_only', 'Max_Temp', 'Min_Temp', 'Weather_Humidity', 'Total_Precipitation']

# Prepare crop data for merge
df_base['Date_only'] = df_base['synthetic_date'].dt.date

# Merge with weather data
df_base = df_base.merge(df_weather_agg, on='Date_only', how='left')

# Fill missing weather data with seasonal averages or forward fill
for col in ['Max_Temp', 'Min_Temp', 'Weather_Humidity', 'Total_Precipitation']:
    df_base[col].fillna(method='ffill', inplace=True)
    df_base[col].fillna(df_base[col].mean(), inplace=True)

# Create Rain_Expected
df_base['Rain_Expected'] = (df_base['Total_Precipitation'] > 0).astype(int)

print(f"✓ Weather data merged")
print(f"Rain_Expected distribution: {dict(df_base['Rain_Expected'].value_counts())}")

# ============================================
# STEP 4: Create Final Decision Base Dataset
# ============================================
print("\n" + "="*50)
print("STEP 4: Create Final Decision Base Dataset")
print("="*50)

# Select final columns
final_columns = [
    'Soil_Moisture',
    'Moisture_Trend', 
    'Temperature',
    'Humidity',
    'Rain_Expected',
    'Crop'
]

decision_base = df_base[final_columns].copy()

# Ensure proper data types
for col in ['Soil_Moisture', 'Moisture_Trend', 'Temperature', 'Humidity']:
    decision_base[col] = decision_base[col].astype(float)

decision_base['Rain_Expected'] = decision_base['Rain_Expected'].astype(int)

# Remove duplicates and clean
decision_base = decision_base.drop_duplicates().reset_index(drop=True)

print(f"✓ Final dataset created: {decision_base.shape}")
print(f"\nDataset Summary:")
print(decision_base.describe())

print(f"\nCrop distribution:")
print(decision_base['Crop'].value_counts().head(10))

# ============================================
# SAVE DELIVERABLE
# ============================================
print("\n" + "="*50)
print("SAVING CORRECTED DELIVERABLE")
print("="*50)

output_path = r'c:\Users\sadwi\OneDrive\Desktop\Data\decision_base_corrected.csv'
decision_base.to_csv(output_path, index=False)

print(f"✓ decision_base_corrected.csv saved to: {output_path}")
print(f"✓ Total rows: {len(decision_base)} (FULL DATASET!)")
print(f"✓ Total columns: {len(decision_base.columns)}")

print("\n" + "="*50)
print("SAMPLE OUTPUT (First 10 rows)")
print("="*50)
print(decision_base.head(10).to_string())

print("\n" + "="*50)
print("✓ CORRECTED MEMBER A TASK COMPLETED")
print(f"✓ NOW USING ALL {len(decision_base)} RECORDS!")
print("="*50)