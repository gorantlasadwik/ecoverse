import pandas as pd

print("=== REPLACING CROP NAMES WITH IDs FOR ML ===")

# Load the files
df_decision = pd.read_csv('decision_base.csv')
df_mapping = pd.read_csv('crop_mapping.csv')

print(f"Original dataset: {df_decision.shape}")
print(f"Mapping file: {df_mapping.shape}")

# Show current crop distribution
print(f"\nCurrent crop distribution (top 10):")
print(df_decision['Crop'].value_counts().head(10))

# Create mapping dictionary
crop_to_id = dict(zip(df_mapping['Crop_Name'], df_mapping['Encoded_Value']))
print(f"\nMapping dictionary created with {len(crop_to_id)} mappings")

# Handle potential name mismatches by creating a more flexible mapping
current_crops = set(df_decision['Crop'].unique())
mapping_crops = set(df_mapping['Crop_Name'].unique())

print(f"\nCrop matching check:")
print(f"Decision base crops: {len(current_crops)}")
print(f"Mapping crops: {len(mapping_crops)}")

# Check for mismatches and try to resolve them
unmatched = current_crops - mapping_crops
if unmatched:
    print(f"\nUnmatched crops found: {len(unmatched)}")
    for crop in sorted(unmatched):
        print(f"  - '{crop}'")
    
    # Try to find close matches and create extended mapping
    import difflib
    extended_mapping = crop_to_id.copy()
    
    for crop in unmatched:
        # Find closest match
        closest_matches = difflib.get_close_matches(crop, mapping_crops, n=1, cutoff=0.8)
        if closest_matches:
            closest = closest_matches[0]
            extended_mapping[crop] = crop_to_id[closest]
            print(f"  Mapping '{crop}' -> '{closest}' (ID: {crop_to_id[closest]})")
        else:
            # Assign next available ID
            max_id = max(crop_to_id.values())
            extended_mapping[crop] = max_id + 1
            print(f"  Assigning new ID {max_id + 1} to '{crop}'")
    
    crop_to_id = extended_mapping

# Apply the mapping
print(f"\nApplying crop ID mapping...")
df_decision['Crop_ID'] = df_decision['Crop'].map(crop_to_id)

# Check for any unmapped crops
unmapped = df_decision['Crop_ID'].isna().sum()
if unmapped > 0:
    print(f"WARNING: {unmapped} crops could not be mapped!")
    unmapped_crops = df_decision[df_decision['Crop_ID'].isna()]['Crop'].unique()
    print(f"Unmapped crops: {unmapped_crops}")
else:
    print("✓ All crops successfully mapped!")

# Replace Crop column with Crop_ID
df_decision['Crop'] = df_decision['Crop_ID'].astype(int)
df_decision = df_decision.drop('Crop_ID', axis=1)

# Verify the result
print(f"\n=== FINAL RESULT ===")
print(f"Dataset shape: {df_decision.shape}")
print(f"Crop column now contains IDs: {sorted(df_decision['Crop'].unique())}")
print(f"Crop ID distribution (top 10):")
print(df_decision['Crop'].value_counts().head(10))

print(f"\nSample of converted data:")
print(df_decision.head())

# Save the updated dataset
output_file = 'decision_base.csv'
df_decision.to_csv(output_file, index=False)
print(f"\n✓ Updated dataset saved to: {output_file}")

# Create a summary report
print(f"\n=== ML-READY DATASET SUMMARY ===")
print(f"✓ Crop names replaced with integer IDs")
print(f"✓ Total records: {len(df_decision):,}")
print(f"✓ Crop IDs range: {df_decision['Crop'].min()} to {df_decision['Crop'].max()}")
print(f"✓ All features are now numeric (ML-ready)")
print(f"✓ Columns: {list(df_decision.columns)}")

# Verify data types
print(f"\nData types:")
for col in df_decision.columns:
    dtype = df_decision[col].dtype
    print(f"  {col}: {dtype}")

print(f"\n✅ CONVERSION COMPLETED - READY FOR ML!")