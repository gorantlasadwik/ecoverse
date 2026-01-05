import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================
# MEMBER A - Base Dataset & Weather Integration
# ============================================

print("Loading datasets...")

# Load datasets
try:
    # Dataset 4: Smart Farming IoT Sensor Data (Primary source)
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
# STEP 1: Clean IoT Sensor Data
# ============================================
print("\n" + "="*50)
print("STEP 1: Clean IoT Sensor Data")
print("="*50)

# Select relevant columns and create base table
base_columns = {
    'soil_moisture_%': 'Soil_Moisture',
    'temperature_C': 'Temperature',
    'humidity_%': 'Humidity',
    'rainfall_mm': 'Rainfall',
    'crop_type': 'Crop',
    'timestamp': 'timestamp'
}

df_base = df_iot[list(base_columns.keys())].copy()
df_base.rename(columns=base_columns, inplace=True)

# Handle missing values
print(f"Missing values before cleaning:")
print(df_base.isnull().sum())

# Fill missing values with column means
for col in df_base.select_dtypes(include=[np.number]).columns:
    df_base[col].fillna(df_base[col].mean(), inplace=True)

# Remove any remaining rows with missing values
df_base = df_base.dropna()

# Encode Crop as categorical
df_base['Crop_encoded'] = pd.Categorical(df_base['Crop']).codes
crops_mapping = dict(enumerate(df_base['Crop'].astype('category').cat.categories))
print(f"\nCrop Categories: {crops_mapping}")

print(f"✓ Base table created: {df_base.shape}")
print(f"\nBase table columns: {df_base.columns.tolist()}")
print(f"Sample data:\n{df_base.head()}")

# ============================================
# STEP 2: Integrate Additional Sensor Data
# ============================================
print("\n" + "="*50)
print("STEP 2: Integrate Additional Sensor Data")
print("="*50)

# Normalize units for Dataset 5
# Dataset 5 has: weather_temperature, weather_humidity, solar_radiation, soil_moisture, soil_temperature
df_sensors_clean = df_sensors.copy()
df_sensors_clean = df_sensors_clean[df_sensors_clean['soil_moisture'].notna()]

# Convert soil_moisture to numeric
df_sensors_clean['soil_moisture_norm'] = pd.to_numeric(df_sensors_clean['soil_moisture'], errors='coerce')
df_sensors_clean = df_sensors_clean.dropna(subset=['soil_moisture_norm'])

# Calculate moisture trend as rate of change
window_size = 5  # 5-row rolling window

# Method: Calculate change from previous readings
df_sensors_clean['moisture_diff'] = df_sensors_clean['soil_moisture_norm'].diff()

# Calculate moisture trend as rate of change (percentage change)
df_sensors_clean['Moisture_Trend_raw'] = (
    df_sensors_clean['soil_moisture_norm'].pct_change() * 100
).fillna(0)

# Smooth with rolling mean
df_sensors_clean['Moisture_Trend'] = df_sensors_clean['Moisture_Trend_raw'].rolling(
    window=window_size, min_periods=1
).mean()

print(f"✓ Moisture trend calculated")
print(f"Moisture Trend stats:\n{df_sensors_clean['Moisture_Trend'].describe()}")

# Calculate average moisture trend from dataset
if df_sensors_clean['Moisture_Trend'].notna().sum() > 0:
    avg_moisture_trend = df_sensors_clean['Moisture_Trend'].mean()
else:
    # Fallback: calculate from raw differences
    avg_moisture_trend = df_sensors_clean['moisture_diff'].mean()

# If still NaN, use a default
if pd.isna(avg_moisture_trend):
    avg_moisture_trend = 0.0

print(f"Average Moisture Trend: {avg_moisture_trend:.4f}")

# For more granular approach: assign moisture trend per crop based on readings
# Create groups for each observation in base dataset
moisture_trend_values = df_sensors_clean['Moisture_Trend'].fillna(0).values

# Distribute moisture trend values across base dataset
if len(moisture_trend_values) > 0:
    # Create a repeating pattern if dataset is smaller
    trend_array = np.tile(
        moisture_trend_values, 
        (len(df_base) // len(moisture_trend_values) + 1)
    )[:len(df_base)]
    df_base['Moisture_Trend'] = trend_array
else:
    # Fallback to constant value
    df_base['Moisture_Trend'] = avg_moisture_trend

print(f"✓ Moisture trend added to base table")

# ============================================
# STEP 3: Merge Weather Data
# ============================================
print("\n" + "="*50)
print("STEP 3: Merge Weather Data")
print("="*50)

# Parse date columns
df_weather['Date'] = pd.to_datetime(df_weather['Date'])
df_base['timestamp_dt'] = pd.to_datetime(df_base['timestamp'])

print(f"Weather data date range: {df_weather['Date'].min()} to {df_weather['Date'].max()}")
print(f"IoT data date range: {df_base['timestamp_dt'].min()} to {df_base['timestamp_dt'].max()}")

# Create weather aggregated by date
df_weather_agg = df_weather.copy()
df_weather_agg['Date_only'] = df_weather_agg['Date'].dt.date
df_weather_agg = df_weather_agg.groupby('Date_only').agg({
    'MaxT': 'mean',
    'MinT': 'mean',
    'Humidity ': 'mean',
    'Precipitation': 'sum'
}).reset_index()

df_weather_agg.columns = ['Date_only', 'Max_Temp', 'Min_Temp', 'Avg_Humidity', 'Total_Precipitation']

# Create date column for IoT data
df_base['Date_only'] = df_base['timestamp_dt'].dt.date

# Merge IoT with weather data on date
df_base = df_base.merge(
    df_weather_agg,
    on='Date_only',
    how='left'
)

# For unmatched dates, forward/backward fill
df_base['Max_Temp'].fillna(method='ffill', inplace=True)
df_base['Min_Temp'].fillna(method='ffill', inplace=True)
df_base['Avg_Humidity'].fillna(method='ffill', inplace=True)
df_base['Total_Precipitation'].fillna(method='ffill', inplace=True)

# Handle any remaining NaNs with the mean
for col in ['Max_Temp', 'Min_Temp', 'Avg_Humidity', 'Total_Precipitation']:
    df_base[col].fillna(df_base[col].mean(), inplace=True)

# Calculate Avg_Temp
df_base['Avg_Temp'] = (df_base['Max_Temp'] + df_base['Min_Temp']) / 2

# Create Rain_Expected (binary: 1 if precipitation > 0)
df_base['Rain_Expected'] = (df_base['Total_Precipitation'] > 0).astype(int)

print(f"✓ Weather data merged")
print(f"Rain_Expected distribution:\n{df_base['Rain_Expected'].value_counts()}")

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

# Ensure numeric columns are float
for col in ['Soil_Moisture', 'Moisture_Trend', 'Temperature', 'Humidity']:
    decision_base[col] = decision_base[col].astype(float)

decision_base['Rain_Expected'] = decision_base['Rain_Expected'].astype(int)

# Remove any remaining duplicates
decision_base = decision_base.drop_duplicates().reset_index(drop=True)

print(f"✓ Final dataset created: {decision_base.shape}")
print(f"\nFinal columns: {decision_base.columns.tolist()}")
print(f"\nDataset Summary:")
print(decision_base.describe())

print(f"\nCrop distribution:")
print(decision_base['Crop'].value_counts())

# ============================================
# SAVE DELIVERABLE
# ============================================
print("\n" + "="*50)
print("SAVING DELIVERABLE")
print("="*50)

output_path = r'c:\Users\sadwi\OneDrive\Desktop\Data\decision_base.csv'
decision_base.to_csv(output_path, index=False)

print(f"✓ decision_base.csv saved to: {output_path}")
print(f"✓ Total rows: {len(decision_base)}")
print(f"✓ Total columns: {len(decision_base.columns)}")

print("\n" + "="*50)
print("SAMPLE OUTPUT (First 10 rows)")
print("="*50)
print(decision_base.head(10).to_string())

print("\n" + "="*50)
print("✓ MEMBER A TASK COMPLETED SUCCESSFULLY")
print("="*50)
