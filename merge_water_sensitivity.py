import pandas as pd
import numpy as np

print("=== MERGING WATER SENSITIVITY DATA WITH EXTENDED DATASET ===")

# Read the datasets
print("Loading datasets...")
extended_names = pd.read_csv('decision_base_extended_with_names.csv')
extended_ids = pd.read_csv('decision_base_extended_with_ids.csv')
water_sensitivity = pd.read_csv('crop_mapping_with_water_sensitivity.csv')

print(f"✓ Extended dataset (names): {len(extended_names)} records")
print(f"✓ Extended dataset (IDs): {len(extended_ids)} records")
print(f"✓ Water sensitivity mapping: {len(water_sensitivity)} crops")

print("\n=== PREPARING MERGE ===")
# Clean crop names for better matching
def clean_crop_name(name):
    """Clean crop names for consistent matching"""
    if pd.isna(name):
        return name
    
    # Convert to string and clean
    name = str(name).strip()
    
    # Handle common variations
    name_mapping = {
        'Cotton(Lint)': 'Cotton(lint)',
        'Black Pepper': 'Black pepper',
        'Moong(Green Gram)': 'Moong(Green Gram)'
    }
    
    return name_mapping.get(name, name)

# Clean crop names in both datasets
extended_names['Crop_Clean'] = extended_names['Crop'].apply(clean_crop_name)
water_sensitivity['Crop_Name_Clean'] = water_sensitivity['Crop_Name'].apply(clean_crop_name)

print("✓ Cleaned crop names for matching")

# Check matching before merge
extended_crops = set(extended_names['Crop_Clean'].unique())
mapping_crops = set(water_sensitivity['Crop_Name_Clean'].unique())

print(f"\n=== MATCHING ANALYSIS ===")
print(f"Crops in extended dataset: {len(extended_crops)}")
print(f"Crops in water sensitivity: {len(mapping_crops)}")
print(f"Common crops: {len(extended_crops.intersection(mapping_crops))}")

# Show unmatched crops
unmatched = extended_crops - mapping_crops
if unmatched:
    print(f"⚠️  Unmatched crops in extended dataset: {sorted(unmatched)}")

print("\n=== MERGING DATA ===")
# Merge with water sensitivity data
merged_names = extended_names.merge(
    water_sensitivity[['Crop_Name_Clean', 'Encoded_Value', 'Water_Sensitivity']], 
    left_on='Crop_Clean', 
    right_on='Crop_Name_Clean', 
    how='left'
)

# Drop the temporary cleaning columns
merged_names = merged_names.drop(['Crop_Clean', 'Crop_Name_Clean'], axis=1)

# For the IDs version, we already have the encoded values, so just add Water_Sensitivity
# First, create a mapping from ID to Water_Sensitivity
id_to_water = dict(zip(water_sensitivity['Encoded_Value'], water_sensitivity['Water_Sensitivity']))

# Add Water_Sensitivity to the IDs dataset
extended_ids['Water_Sensitivity'] = extended_ids['Crop'].map(id_to_water)

print(f"✓ Merged names dataset: {len(merged_names)} records")
print(f"✓ Added water sensitivity to IDs dataset: {len(extended_ids)} records")

print("\n=== REORDERING COLUMNS ===")
# Reorder columns for better organization
names_columns = [
    'soil_moisture', 'soil_temperature', 'weather_temperature', 'weather_humidity', 
    'solar_radiation', 'MaxT', 'MinT', 'Precipitation', 'Moisture_Trend', 
    'Crop', 'Encoded_Value', 'Water_Sensitivity'
]

ids_columns = [
    'soil_moisture', 'soil_temperature', 'weather_temperature', 'weather_humidity', 
    'solar_radiation', 'MaxT', 'MinT', 'Precipitation', 'Moisture_Trend', 
    'Crop', 'Water_Sensitivity'
]

merged_names = merged_names[names_columns]
extended_ids = extended_ids[ids_columns]

print("✓ Columns reordered")

print("\n=== SAVING ENHANCED DATASETS ===")
# Save the enhanced datasets
merged_names.to_csv('decision_base_extended_with_water_sensitivity_names.csv', index=False)
extended_ids.to_csv('decision_base_extended_with_water_sensitivity_ids.csv', index=False)

print("✅ Saved decision_base_extended_with_water_sensitivity_names.csv")
print("✅ Saved decision_base_extended_with_water_sensitivity_ids.csv")

print("\n=== FINAL SUMMARY ===")
print(f"📊 Records: {len(merged_names)}")
print(f"📊 Features: {len(merged_names.columns)}")
print(f"📊 Water Sensitivity levels: {sorted(merged_names['Water_Sensitivity'].dropna().unique())}")

print(f"\n📋 Water Sensitivity Distribution:")
print(merged_names['Water_Sensitivity'].value_counts().sort_index())

print(f"\n📋 Sample data (with water sensitivity):")
print(merged_names[['Crop', 'Encoded_Value', 'Water_Sensitivity', 'soil_moisture', 'Precipitation']].head())

# Check for any missing water sensitivity values
missing_water = merged_names['Water_Sensitivity'].isna().sum()
if missing_water > 0:
    print(f"\n⚠️  Warning: {missing_water} records have missing water sensitivity data")
    print("Crops with missing water sensitivity:")
    missing_crops = merged_names[merged_names['Water_Sensitivity'].isna()]['Crop'].unique()
    print(missing_crops)
else:
    print(f"\n✅ All records have water sensitivity data!")

print("\n🎯 ENHANCED DATASETS READY FOR ML WITH WATER SENSITIVITY!")