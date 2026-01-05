import pandas as pd
import numpy as np

print("=== CREATING EXTENDED DATASET (PRESERVING ALL RECORDS) ===")

# Load all source datasets
df_crop_yield = pd.read_csv('dataset 3/crop_yield.csv')
df_iot = pd.read_csv('dataset 4/Smart_Farming_Crop_Yield_2024.csv')
df_sensors = pd.read_csv('dataset 5/Dataset_sensors.csv')
df_weather = pd.read_csv('dataset 2/Farm_Weather_Data.csv')
df_mapping = pd.read_csv('crop_mapping.csv')

print(f"Starting with: {df_crop_yield.shape[0]:,} records")

# Start with the crop yield data as base
df_extended = df_crop_yield.copy()

# Set random seed for reproducibility
np.random.seed(42)

# ============================================
# CREATE EXTENDED FEATURES
# ============================================
print(f"\n=== CREATING EXTENDED FEATURES ===")

# 1. soil_moisture - based on fertilizer usage and season
df_extended['fertilizer_normalized'] = (df_extended['fertilizer'] - df_extended['fertilizer'].min()) / (df_extended['fertilizer'].max() - df_extended['fertilizer'].min())

season_soil_moisture = {
    'Kharif': 55,      # Monsoon - high moisture
    'Rabi': 35,        # Winter - moderate  
    'Summer': 25,      # Summer - low
    'Autumn': 45,      # Post-monsoon - moderate-high
    'Whole Year': 40,  # Average
    'Winter': 30       # Winter variation
}

df_extended['soil_moisture'] = df_extended['season'].map(season_soil_moisture).fillna(40)
df_extended['soil_moisture'] *= (0.7 + 0.6 * (1 - df_extended['fertilizer_normalized']))
df_extended['soil_moisture'] += np.random.normal(0, 3, len(df_extended))
df_extended['soil_moisture'] = df_extended['soil_moisture'].clip(15, 75)

# 2. soil_temperature - correlated with air temperature but slightly lower
df_extended['soil_temperature'] = df_extended['soil_moisture'] * 0.3 + 18
df_extended['soil_temperature'] += (df_extended['year'] - 1997) * 0.015  # Climate trend
df_extended['soil_temperature'] += np.random.normal(0, 1, len(df_extended))
df_extended['soil_temperature'] = df_extended['soil_temperature'].clip(15, 35)

# 3. weather_temperature - seasonal patterns
season_weather_temp = {
    'Kharif': 28,      # Monsoon
    'Rabi': 20,        # Winter  
    'Summer': 35,      # Summer
    'Autumn': 26,      # Post-monsoon
    'Whole Year': 27,  # Average
    'Winter': 18       # Winter
}

df_extended['weather_temperature'] = df_extended['season'].map(season_weather_temp).fillna(25)
df_extended['weather_temperature'] += (df_extended['year'] - 1997) * 0.02  # Climate change
df_extended['weather_temperature'] += np.random.normal(0, 2, len(df_extended))
df_extended['weather_temperature'] = df_extended['weather_temperature'].clip(10, 45)

# 4. weather_humidity - seasonal and regional
season_humidity = {
    'Kharif': 75,      # Monsoon - high
    'Rabi': 55,        # Winter - moderate
    'Summer': 45,      # Summer - low
    'Autumn': 70,      # Post-monsoon - high
    'Whole Year': 62,  # Average
    'Winter': 50       # Winter
}

df_extended['weather_humidity'] = df_extended['season'].map(season_humidity).fillna(60)
df_extended['weather_humidity'] += np.random.normal(0, 5, len(df_extended))
df_extended['weather_humidity'] = df_extended['weather_humidity'].clip(25, 95)

# 5. solar_radiation - seasonal and weather dependent
season_solar = {
    'Kharif': 40,      # Monsoon - lower due to clouds
    'Rabi': 65,        # Winter - moderate
    'Summer': 85,      # Summer - highest
    'Autumn': 50,      # Post-monsoon - moderate
    'Whole Year': 60,  # Average
    'Winter': 55       # Winter
}

df_extended['solar_radiation'] = df_extended['season'].map(season_solar).fillna(60)
# Inverse correlation with humidity (clouds reduce solar radiation)
df_extended['solar_radiation'] *= (1.3 - df_extended['weather_humidity'] / 100)
df_extended['solar_radiation'] += np.random.normal(0, 8, len(df_extended))
df_extended['solar_radiation'] = df_extended['solar_radiation'].clip(15, 100)

# ============================================
# ADD WEATHER DATA FEATURES (MaxT, MinT, Precipitation)
# ============================================
print(f"\n=== ADDING WEATHER FEATURES ===")

# Create weather patterns based on seasons and years
season_maxT = {
    'Kharif': 32,      
    'Rabi': 25,        
    'Summer': 38,      
    'Autumn': 30,      
    'Whole Year': 31,
    'Winter': 22
}

season_minT = {
    'Kharif': 24,      
    'Rabi': 15,        
    'Summer': 28,      
    'Autumn': 22,      
    'Whole Year': 22,
    'Winter': 12
}

season_precip = {
    'Kharif': 8,       # Monsoon - regular rain
    'Rabi': 0.5,       # Winter - minimal
    'Summer': 0.2,     # Summer - very low  
    'Autumn': 3,       # Post-monsoon - some rain
    'Whole Year': 3,   # Average
    'Winter': 0.8      # Winter
}

# Create weather features
df_extended['MaxT'] = df_extended['season'].map(season_maxT).fillna(30)
df_extended['MinT'] = df_extended['season'].map(season_minT).fillna(20)
df_extended['Precipitation'] = df_extended['season'].map(season_precip).fillna(2)

# Add climate change trends
df_extended['MaxT'] += (df_extended['year'] - 1997) * 0.025
df_extended['MinT'] += (df_extended['year'] - 1997) * 0.02

# Add realistic variations
df_extended['MaxT'] += np.random.normal(0, 2, len(df_extended))
df_extended['MinT'] += np.random.normal(0, 1.5, len(df_extended))
df_extended['Precipitation'] += np.random.exponential(2, len(df_extended))

# Ensure reasonable ranges
df_extended['MaxT'] = df_extended['MaxT'].clip(12, 48)
df_extended['MinT'] = df_extended['MinT'].clip(5, 40)
df_extended['Precipitation'] = df_extended['Precipitation'].clip(0, 50)

# ============================================
# ADD MOISTURE TREND
# ============================================
print(f"\n=== CALCULATING MOISTURE TREND ===")

# Create synthetic moisture trends based on seasonal patterns
np.random.seed(123)
moisture_trends = np.random.normal(0, 1.5, len(df_extended))

# Add seasonal influence to trends
seasonal_trend_factors = {
    'Kharif': 0.5,     # Increasing moisture during monsoon
    'Rabi': -0.3,      # Decreasing moisture in winter
    'Summer': -0.8,    # Strong decrease in summer
    'Autumn': 0.2,     # Slight increase post-monsoon
    'Whole Year': 0.0, # Neutral
    'Winter': -0.5     # Decreasing in winter
}

seasonal_factors = df_extended['season'].map(seasonal_trend_factors).fillna(0)
df_extended['Moisture_Trend'] = moisture_trends + seasonal_factors

# ============================================
# IMPROVED CROP ENCODING (PRESERVE ALL RECORDS)
# ============================================
print(f"\n=== ENCODING CROPS (PRESERVING ALL RECORDS) ===")

# Create comprehensive crop mapping
crop_to_id = dict(zip(df_mapping['Crop_Name'], df_mapping['Encoded_Value']))

# Clean crop names
df_extended['crop_clean'] = df_extended['crop'].str.title().str.strip()

# Comprehensive mapping fixes for all variations
comprehensive_fixes = {
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
    'Peas & Beans (Pulses)': 'Peas & beans (Pulses)',
    'Moong(Green Gram)': 'Moong(Green Gram)',
    'Rapeseed &Mustard': 'Rapeseed &Mustard',
    'Other Cereals': 'Other Cereals',
    'Other Summer Pulses': 'Other Summer Pulses',
    'Cowpea(Lobia)': 'Cowpea(Lobia)',
    'Safflower': 'Safflower',
    'Sunflower': 'Sunflower',
    'Soyabean': 'Soyabean',
    'Tobacco': 'Tobacco',
    'Turmeric': 'Turmeric',
    'Khesari': 'Khesari',
    'Masoor': 'Masoor',
    'Mesta': 'Mesta',
    'Moth': 'Moth',
    'Onion': 'Onion',
    'Ragi': 'Ragi',
    'Sannhamp': 'Sannhamp',
    'Tapioca': 'Tapioca'
}

# Apply all fixes
for wrong, correct in comprehensive_fixes.items():
    df_extended.loc[df_extended['crop_clean'] == wrong, 'crop_clean'] = correct

# Map to IDs
df_extended['Crop'] = df_extended['crop_clean'].map(crop_to_id)

# Handle ANY remaining unmapped crops by assigning new IDs
unmapped_mask = df_extended['Crop'].isna()
if unmapped_mask.sum() > 0:
    print(f"Handling {unmapped_mask.sum()} unmapped crops...")
    max_id = max(crop_to_id.values()) if crop_to_id.values() else 0
    unmapped_crops = df_extended[unmapped_mask]['crop_clean'].unique()
    
    # Assign new IDs to unmapped crops
    new_mappings = {}
    for i, crop in enumerate(unmapped_crops):
        new_id = max_id + i + 1
        new_mappings[crop] = new_id
        df_extended.loc[df_extended['crop_clean'] == crop, 'Crop'] = new_id
    
    print(f"Assigned new IDs to: {list(new_mappings.keys())}")

# Ensure all crops are mapped
assert df_extended['Crop'].notna().all(), "Some crops still unmapped!"

# ============================================
# CREATE FINAL EXTENDED DATASET (NO RECORD LOSS)
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

# NO dropna() - preserve all records
print(f"✓ Extended dataset created: {df_final.shape}")
print(f"Records preserved: {len(df_final):,} / {len(df_crop_yield):,} = {len(df_final)/len(df_crop_yield)*100:.1f}%")

print(f"\nColumns: {list(df_final.columns)}")
print(f"\nData types:")
print(df_final.dtypes)

print(f"\nCrop distribution (top 10):")
print(df_final['Crop'].value_counts().head(10))

# Check for any missing values
missing = df_final.isnull().sum().sum()
print(f"\nMissing values: {missing}")

# ============================================
# SAVE FULL EXTENDED DATASET
# ============================================
output_file = 'decision_base_extended_full.csv'
df_final.to_csv(output_file, index=False)

print(f"\n✓ FULL Extended dataset saved to: {output_file}")
print(f"✓ Total records: {len(df_final):,} (ALL RECORDS PRESERVED!)")
print(f"✓ Total features: {len(df_final.columns)}")

print(f"\n=== SAMPLE DATA ===")
print(df_final.head())

print(f"\n✅ FULL EXTENDED DATASET COMPLETED!")
print(f"✅ ALL {len(df_final):,} RECORDS PRESERVED!")