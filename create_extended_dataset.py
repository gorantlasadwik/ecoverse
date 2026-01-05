import pandas as pd
import numpy as np

print("=== CREATING EXTENDED DATASET WITH ADDITIONAL FEATURES ===")

# Load all source datasets
df_crop_yield = pd.read_csv('dataset 3/crop_yield.csv')
df_iot = pd.read_csv('dataset 4/Smart_Farming_Crop_Yield_2024.csv')
df_sensors = pd.read_csv('dataset 5/Dataset_sensors.csv')
df_weather = pd.read_csv('dataset 2/Farm_Weather_Data.csv')
df_mapping = pd.read_csv('crop_mapping.csv')

print(f"Loaded datasets:")
print(f"- Crop yield: {df_crop_yield.shape}")
print(f"- IoT farming: {df_iot.shape}")
print(f"- Sensors: {df_sensors.shape}")
print(f"- Weather: {df_weather.shape}")

# Start with the crop yield data as base (19k records)
df_extended = df_crop_yield.copy()
print(f"\nBase dataset: {df_extended.shape}")

# ============================================
# EXTRACT SENSOR DATA FEATURES
# ============================================
print(f"\n=== EXTRACTING SENSOR FEATURES ===")

# From Dataset 5 - get sensor statistics for distribution
# Convert columns to numeric first
for col in ['soil_moisture', 'soil_temperature', 'weather_temperature', 'weather_humidity', 'solar_radiation']:
    if col in df_sensors.columns:
        df_sensors[col] = pd.to_numeric(df_sensors[col], errors='coerce')

sensors_clean = df_sensors.dropna()
print(f"Clean sensor data: {sensors_clean.shape}")

# Define default ranges if data is missing
default_ranges = {
    'soil_moisture': (40, 70),
    'soil_temperature': (20, 30), 
    'weather_temperature': (15, 40),
    'weather_humidity': (40, 90),
    'solar_radiation': (20, 100)
}

# Get actual stats or use defaults
sensor_stats = {}
for col, (min_val, max_val) in default_ranges.items():
    if col in sensors_clean.columns and not sensors_clean[col].empty:
        stats = sensors_clean[col].describe()
        sensor_stats[col] = (stats['min'], stats['max'])
        print(f"{col} stats: {stats['min']:.2f} - {stats['max']:.2f}")
    else:
        sensor_stats[col] = (min_val, max_val)
        print(f"{col} stats (default): {min_val} - {max_val}")

# ============================================
# CREATE EXTENDED FEATURES
# ============================================
print(f"\n=== CREATING EXTENDED FEATURES ===")

# Set random seed for reproducibility
np.random.seed(42)

# 1. soil_moisture - based on fertilizer usage and season
df_extended['fertilizer_normalized'] = (df_extended['fertilizer'] - df_extended['fertilizer'].min()) / (df_extended['fertilizer'].max() - df_extended['fertilizer'].min())

season_soil_moisture = {
    'Kharif': 55,      # Monsoon - high moisture
    'Rabi': 35,        # Winter - moderate  
    'Summer': 25,      # Summer - low
    'Autumn': 45,      # Post-monsoon - moderate-high
    'Whole Year': 40   # Average
}

df_extended['soil_moisture'] = df_extended['season'].map(season_soil_moisture).fillna(40)
df_extended['soil_moisture'] *= (0.7 + 0.6 * (1 - df_extended['fertilizer_normalized']))  # Fertilizer correlation
df_extended['soil_moisture'] += np.random.normal(0, 3, len(df_extended))
df_extended['soil_moisture'] = df_extended['soil_moisture'].clip(sensor_stats['soil_moisture'][0], sensor_stats['soil_moisture'][1])

# 2. soil_temperature - correlated with air temperature but slightly lower
df_extended['soil_temperature'] = df_extended['soil_moisture'] * 0.4 + 15  # Base correlation
df_extended['soil_temperature'] += (df_extended['year'] - 1997) * 0.015  # Climate trend
df_extended['soil_temperature'] += np.random.normal(0, 1, len(df_extended))
df_extended['soil_temperature'] = df_extended['soil_temperature'].clip(sensor_stats['soil_temperature'][0], sensor_stats['soil_temperature'][1])

# 3. weather_temperature - seasonal patterns
season_weather_temp = {
    'Kharif': 28,      # Monsoon
    'Rabi': 20,        # Winter  
    'Summer': 35,      # Summer
    'Autumn': 26,      # Post-monsoon
    'Whole Year': 27   # Average
}

df_extended['weather_temperature'] = df_extended['season'].map(season_weather_temp).fillna(27)
df_extended['weather_temperature'] += (df_extended['year'] - 1997) * 0.02  # Climate change
df_extended['weather_temperature'] += np.random.normal(0, 2, len(df_extended))
df_extended['weather_temperature'] = df_extended['weather_temperature'].clip(sensor_stats['weather_temperature'][0], sensor_stats['weather_temperature'][1])

# 4. weather_humidity - seasonal and regional
season_humidity = {
    'Kharif': 75,      # Monsoon - high
    'Rabi': 55,        # Winter - moderate
    'Summer': 45,      # Summer - low
    'Autumn': 70,      # Post-monsoon - high
    'Whole Year': 62   # Average
}

df_extended['weather_humidity'] = df_extended['season'].map(season_humidity).fillna(62)
df_extended['weather_humidity'] += np.random.normal(0, 5, len(df_extended))
df_extended['weather_humidity'] = df_extended['weather_humidity'].clip(sensor_stats['weather_humidity'][0], sensor_stats['weather_humidity'][1])

# 5. solar_radiation - seasonal and weather dependent
season_solar = {
    'Kharif': 40,      # Monsoon - lower due to clouds
    'Rabi': 65,        # Winter - moderate
    'Summer': 85,      # Summer - highest
    'Autumn': 50,      # Post-monsoon - moderate
    'Whole Year': 60   # Average
}

df_extended['solar_radiation'] = df_extended['season'].map(season_solar).fillna(60)
# Inverse correlation with humidity (clouds reduce solar radiation)
df_extended['solar_radiation'] *= (1.3 - df_extended['weather_humidity'] / 100)
df_extended['solar_radiation'] += np.random.normal(0, 8, len(df_extended))
df_extended['solar_radiation'] = df_extended['solar_radiation'].clip(sensor_stats['solar_radiation'][0], sensor_stats['solar_radiation'][1])

# ============================================
# ADD WEATHER DATA FEATURES
# ============================================
print(f"\n=== ADDING WEATHER FEATURES ===")

# Parse weather data
df_weather['Date'] = pd.to_datetime(df_weather['Date'])
weather_stats = df_weather.groupby(df_weather['Date'].dt.date).agg({
    'MaxT': 'mean',
    'MinT': 'mean', 
    'Precipitation': 'sum'
}).reset_index()

# Create synthetic dates for crop data
df_extended['synthetic_date'] = pd.to_datetime(df_extended['year'].astype(str) + '-01-01') + \
                               pd.to_timedelta(np.random.randint(0, 365, len(df_extended)), unit='D')
df_extended['Date'] = df_extended['synthetic_date'].dt.date

# Merge with weather data
df_extended = df_extended.merge(weather_stats, on='Date', how='left')

# Fill missing weather data with seasonal averages
weather_maxT_season = {
    'Kharif': 32,      
    'Rabi': 25,        
    'Summer': 38,      
    'Autumn': 30,      
    'Whole Year': 31   
}

weather_minT_season = {
    'Kharif': 24,      
    'Rabi': 15,        
    'Summer': 28,      
    'Autumn': 22,      
    'Whole Year': 22   
}

weather_precip_season = {
    'Kharif': 8,       # Monsoon - regular rain
    'Rabi': 0.5,       # Winter - minimal
    'Summer': 0.2,     # Summer - very low  
    'Autumn': 3,       # Post-monsoon - some rain
    'Whole Year': 3    # Average
}

# Fill missing values
df_extended['MaxT'] = df_extended['MaxT'].fillna(df_extended['season'].map(weather_maxT_season))
df_extended['MinT'] = df_extended['MinT'].fillna(df_extended['season'].map(weather_minT_season))
df_extended['Precipitation'] = df_extended['Precipitation'].fillna(df_extended['season'].map(weather_precip_season))

# Add climate change trends
df_extended['MaxT'] += (df_extended['year'] - 1997) * 0.025
df_extended['MinT'] += (df_extended['year'] - 1997) * 0.02

# Add realistic variations
df_extended['MaxT'] += np.random.normal(0, 2, len(df_extended))
df_extended['MinT'] += np.random.normal(0, 1.5, len(df_extended))
df_extended['Precipitation'] += np.random.exponential(2, len(df_extended))

# Ensure reasonable ranges
df_extended['MaxT'] = df_extended['MaxT'].clip(15, 45)
df_extended['MinT'] = df_extended['MinT'].clip(5, 35)
df_extended['Precipitation'] = df_extended['Precipitation'].clip(0, 50)

# ============================================
# ADD MOISTURE TREND
# ============================================
print(f"\n=== CALCULATING MOISTURE TREND ===")

# Use sensor data to calculate moisture trends
if 'soil_moisture' in sensors_clean.columns and len(sensors_clean) > 0:
    sensors_clean['moisture_change'] = sensors_clean['soil_moisture'].pct_change() * 100
    sensors_clean['Moisture_Trend'] = sensors_clean['moisture_change'].rolling(window=5, min_periods=1).mean().fillna(0)
    moisture_trends = sensors_clean['Moisture_Trend'].values
    print(f"Using {len(moisture_trends)} moisture trend values from sensors")
else:
    # Create synthetic moisture trends if sensor data is not available
    print("Creating synthetic moisture trends")
    moisture_trends = np.random.normal(0, 1.5, 1000)  # Create 1000 trend values

# Distribute trends across the dataset
if len(moisture_trends) > 0:
    trend_cycles = (len(df_extended) // len(moisture_trends)) + 1
    extended_trends = np.tile(moisture_trends, trend_cycles)[:len(df_extended)]
    df_extended['Moisture_Trend'] = extended_trends
else:
    df_extended['Moisture_Trend'] = np.random.normal(0, 1, len(df_extended))

# ============================================
# ADD CROP ENCODING
# ============================================
print(f"\n=== ENCODING CROPS ===")

# Create crop mapping
crop_to_id = dict(zip(df_mapping['Crop_Name'], df_mapping['Encoded_Value']))

# Handle crop name variations
df_extended['crop_clean'] = df_extended['crop'].str.title().str.strip()

# Map similar crops
crop_mapping_fixes = {
    'Cotton(Lint)': 'Cotton(lint)',
    'Black Pepper': 'Black pepper', 
    'Dry Chillies': 'Dry chillies',
    'Coconut': 'Coconut ',
    'Castor Seed': 'Castor seed',
    'Sweet Potato': 'Sweet potato',
    'Small Millets': 'Small millets',
    'Niger Seed': 'Niger seed',
    'Horse-Gram': 'Horse-gram',
    'Guar Seed': 'Guar seed',
    'Oilseeds Total': 'Oilseeds total',
    'Other  Rabi Pulses': 'Other  Rabi pulses',
    'Other Kharif Pulses': 'Other Kharif pulses',
    'Other Oilseeds': 'other oilseeds',
    'Peas & Beans (Pulses)': 'Peas & beans (Pulses)'
}

for wrong, correct in crop_mapping_fixes.items():
    df_extended.loc[df_extended['crop_clean'] == wrong, 'crop_clean'] = correct

df_extended['Crop'] = df_extended['crop_clean'].map(crop_to_id)

# Handle any remaining unmapped crops
unmapped_mask = df_extended['Crop'].isna()
if unmapped_mask.sum() > 0:
    print(f"Assigning new IDs to {unmapped_mask.sum()} unmapped crops")
    max_id = max(crop_to_id.values())
    unmapped_crops = df_extended[unmapped_mask]['crop_clean'].unique()
    for i, crop in enumerate(unmapped_crops):
        new_id = max_id + i + 1
        df_extended.loc[df_extended['crop_clean'] == crop, 'Crop'] = new_id

# ============================================
# CREATE FINAL EXTENDED DATASET
# ============================================
print(f"\n=== CREATING FINAL EXTENDED DATASET ===")

# Select requested features
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
    'Crop'
]

df_final = df_extended[final_columns].copy()

# Ensure proper data types
for col in final_columns[:-1]:  # All except Crop
    df_final[col] = df_final[col].astype(float)

df_final['Crop'] = df_final['Crop'].astype(int)

# Remove any rows with missing values
df_final = df_final.dropna()

print(f"✓ Extended dataset created: {df_final.shape}")
print(f"\nColumns: {list(df_final.columns)}")
print(f"\nDataset summary:")
print(df_final.describe())

print(f"\nData types:")
print(df_final.dtypes)

print(f"\nCrop distribution (top 10):")
print(df_final['Crop'].value_counts().head(10))

# ============================================
# SAVE EXTENDED DATASET
# ============================================
output_file = 'decision_base_extended.csv'
df_final.to_csv(output_file, index=False)

print(f"\n✓ Extended dataset saved to: {output_file}")
print(f"✓ Total records: {len(df_final):,}")
print(f"✓ Total features: {len(df_final.columns)}")
print(f"✓ All features numeric and ML-ready!")

print(f"\n=== SAMPLE DATA ===")
print(df_final.head(10))

print(f"\n✅ EXTENDED DATASET COMPLETED!")
print(f"Features included: soil_moisture, soil_temperature, weather_temperature, weather_humidity, solar_radiation, MaxT, MinT, Precipitation, Moisture_Trend, Crop")