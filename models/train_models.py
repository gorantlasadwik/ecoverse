"""
Train ML Models for Smart Irrigation System
============================================
This script trains two Decision Tree models:
1. Irrigation Model - Predicts whether irrigation is needed
2. Alert Model - Detects anomalous moisture behavior
"""

import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import joblib
import os

print("="*70)
print("🌱 SMART IRRIGATION SYSTEM - MODEL TRAINING")
print("="*70)

# ============================================
# STEP 1: Load Extended Dataset
# ============================================
print("\n📂 Loading dataset...")

try:
    # Load the extended dataset with water sensitivity
    # Use absolute path or proper relative path
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, '..', 'data', 'decision_base_extended_with_water_sensitivity_ids.csv')
    df = pd.read_csv(data_path)
    print(f"✓ Dataset loaded: {df.shape[0]:,} records, {df.shape[1]} features")
    print(f"✓ Columns: {df.columns.tolist()}")
except FileNotFoundError:
    print("❌ Error: Dataset not found!")
    print("Please ensure 'decision_base_extended_with_water_sensitivity_ids.csv' is in the data/ folder")
    exit(1)

# ============================================
# STEP 2: Feature Engineering
# ============================================
print("\n🔧 Engineering features for ML models...")

# Create target variables based on domain rules

# TARGET 1: Irrigation Decision (binary)
# Logic: Irrigate if soil moisture is low AND no recent rain
df['Irrigate'] = (
    (df['soil_moisture'] < 45) &  # Low soil moisture
    (df['Precipitation'] < 1.0)    # Little to no rain
).astype(int)

# Enhanced irrigation logic with water sensitivity
df['Irrigate'] = np.where(
    (df['Water_Sensitivity'] == 2) & (df['soil_moisture'] < 50),  # High sensitivity crops
    1,
    df['Irrigate']
)

# TARGET 2: Alert Status (binary)
# Logic: Alert if moisture trend is rapidly declining or moisture is critically low
df['Alert'] = (
    (df['Moisture_Trend'] < -2.0) |  # Rapid drying
    (df['soil_moisture'] < 30) |      # Critically low moisture
    ((df['soil_moisture'] < 40) & (df['Precipitation'] < 0.5) & (df['MaxT'] > 38))  # Stress conditions
).astype(int)

print(f"✓ Target variable 'Irrigate' created")
print(f"  - Irrigation needed: {df['Irrigate'].sum():,} records ({df['Irrigate'].mean()*100:.1f}%)")
print(f"  - No irrigation: {(1-df['Irrigate']).sum():,} records ({(1-df['Irrigate'].mean())*100:.1f}%)")

print(f"\n✓ Target variable 'Alert' created")
print(f"  - Alert status: {df['Alert'].sum():,} records ({df['Alert'].mean()*100:.1f}%)")
print(f"  - Normal status: {(1-df['Alert']).sum():,} records ({(1-df['Alert'].mean())*100:.1f}%)")

# ============================================
# STEP 3: Prepare Features for Model A (Irrigation)
# ============================================
print("\n📊 Preparing features for IRRIGATION MODEL...")

# Features for irrigation decision
features_irrigation = [
    'soil_moisture',
    'Moisture_Trend',
    'Precipitation',
    'weather_humidity',
    'MaxT',
    'MinT',
    'Water_Sensitivity'
]

X_irrigation = df[features_irrigation].copy()
y_irrigation = df['Irrigate'].copy()

# Handle missing values
X_irrigation = X_irrigation.fillna(X_irrigation.median())

print(f"✓ Features selected: {features_irrigation}")
print(f"✓ Training samples: {len(X_irrigation):,}")

# ============================================
# STEP 4: Train Irrigation Model (Model A)
# ============================================
print("\n🤖 Training IRRIGATION MODEL (Decision Tree)...")

# Split data
X_train_irr, X_test_irr, y_train_irr, y_test_irr = train_test_split(
    X_irrigation, y_irrigation, test_size=0.2, random_state=42, stratify=y_irrigation
)

print(f"✓ Train set: {len(X_train_irr):,} samples")
print(f"✓ Test set: {len(X_test_irr):,} samples")

# Train Decision Tree
dt_irrigation = DecisionTreeClassifier(
    max_depth=8,
    min_samples_split=50,
    min_samples_leaf=20,
    random_state=42,
    class_weight='balanced'  # Handle class imbalance
)

dt_irrigation.fit(X_train_irr, y_train_irr)
print("✓ Model trained successfully")

# Evaluate
y_pred_irr = dt_irrigation.predict(X_test_irr)
accuracy_irr = accuracy_score(y_test_irr, y_pred_irr)

print(f"\n📈 IRRIGATION MODEL PERFORMANCE:")
print(f"✓ Accuracy: {accuracy_irr*100:.2f}%")
print("\nClassification Report:")
print(classification_report(y_test_irr, y_pred_irr, target_names=['No Irrigation', 'Irrigate']))

# Feature importance
feature_importance_irr = pd.DataFrame({
    'feature': features_irrigation,
    'importance': dt_irrigation.feature_importances_
}).sort_values('importance', ascending=False)

print("\n🔍 Feature Importance (Irrigation Model):")
for idx, row in feature_importance_irr.iterrows():
    print(f"  {row['feature']:25s} {row['importance']:.4f}")

# ============================================
# STEP 5: Prepare Features for Model B (Alert)
# ============================================
print("\n\n📊 Preparing features for ALERT MODEL...")

# Features for alert detection
features_alert = [
    'soil_moisture',
    'Moisture_Trend',
    'soil_temperature',
    'weather_temperature',
    'MaxT',
    'MinT',
    'Precipitation',
    'Water_Sensitivity'
]

X_alert = df[features_alert].copy()
y_alert = df['Alert'].copy()

# Handle missing values
X_alert = X_alert.fillna(X_alert.median())

print(f"✓ Features selected: {features_alert}")
print(f"✓ Training samples: {len(X_alert):,}")

# ============================================
# STEP 6: Train Alert Model (Model B)
# ============================================
print("\n🤖 Training ALERT MODEL (Decision Tree)...")

# Split data
X_train_alert, X_test_alert, y_train_alert, y_test_alert = train_test_split(
    X_alert, y_alert, test_size=0.2, random_state=42, stratify=y_alert
)

print(f"✓ Train set: {len(X_train_alert):,} samples")
print(f"✓ Test set: {len(X_test_alert):,} samples")

# Train Decision Tree
dt_alert = DecisionTreeClassifier(
    max_depth=10,
    min_samples_split=40,
    min_samples_leaf=15,
    random_state=42,
    class_weight='balanced'
)

dt_alert.fit(X_train_alert, y_train_alert)
print("✓ Model trained successfully")

# Evaluate
y_pred_alert = dt_alert.predict(X_test_alert)
accuracy_alert = accuracy_score(y_test_alert, y_pred_alert)

print(f"\n📈 ALERT MODEL PERFORMANCE:")
print(f"✓ Accuracy: {accuracy_alert*100:.2f}%")
print("\nClassification Report:")
print(classification_report(y_test_alert, y_pred_alert, target_names=['Normal', 'Alert']))

# Feature importance
feature_importance_alert = pd.DataFrame({
    'feature': features_alert,
    'importance': dt_alert.feature_importances_
}).sort_values('importance', ascending=False)

print("\n🔍 Feature Importance (Alert Model):")
for idx, row in feature_importance_alert.iterrows():
    print(f"  {row['feature']:25s} {row['importance']:.4f}")

# ============================================
# STEP 7: Save Models
# ============================================
print("\n\n💾 Saving trained models...")

# Save models
joblib.dump(dt_irrigation, 'irrigation_model.pkl')
joblib.dump(dt_alert, 'alert_model.pkl')

# Save feature lists
joblib.dump(features_irrigation, 'irrigation_features.pkl')
joblib.dump(features_alert, 'alert_features.pkl')

print("✓ irrigation_model.pkl saved")
print("✓ alert_model.pkl saved")
print("✓ irrigation_features.pkl saved")
print("✓ alert_features.pkl saved")

# ============================================
# STEP 8: Create Model Info File
# ============================================
model_info = {
    'irrigation_model': {
        'accuracy': accuracy_irr,
        'features': features_irrigation,
        'target': 'Irrigate',
        'classes': ['No Irrigation', 'Irrigate']
    },
    'alert_model': {
        'accuracy': accuracy_alert,
        'features': features_alert,
        'target': 'Alert',
        'classes': ['Normal', 'Alert']
    }
}

joblib.dump(model_info, 'model_info.pkl')
print("✓ model_info.pkl saved")

print("\n" + "="*70)
print("✅ MODEL TRAINING COMPLETE!")
print("="*70)
print(f"\n📊 SUMMARY:")
print(f"  • Irrigation Model Accuracy: {accuracy_irr*100:.2f}%")
print(f"  • Alert Model Accuracy: {accuracy_alert*100:.2f}%")
print(f"  • Models ready for deployment!")
print("\n🚀 Next Step: Run Flask app with 'python app.py'")
print("="*70)
