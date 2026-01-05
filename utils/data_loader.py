"""
Data Loader Utilities for Smart Irrigation System
==================================================
Helper functions to load and preprocess datasets
"""

import pandas as pd
import numpy as np
import os

class DataLoader:
    """Load and manage irrigation datasets"""
    
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.dataset = None
        
    def load_extended_dataset(self, filename='decision_base_extended_with_water_sensitivity_ids.csv'):
        """Load the extended dataset with all features"""
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Dataset not found: {filepath}")
        
        self.dataset = pd.read_csv(filepath)
        print(f"✓ Loaded dataset: {self.dataset.shape[0]:,} records, {self.dataset.shape[1]} features")
        
        return self.dataset
    
    def get_feature_statistics(self):
        """Get statistical summary of all features"""
        if self.dataset is None:
            raise ValueError("Dataset not loaded. Call load_extended_dataset() first.")
        
        stats = self.dataset.describe()
        return stats
    
    def get_sample_records(self, n=5, random=True):
        """Get sample records from the dataset"""
        if self.dataset is None:
            raise ValueError("Dataset not loaded. Call load_extended_dataset() first.")
        
        if random:
            return self.dataset.sample(n=n)
        else:
            return self.dataset.head(n)
    
    def get_feature_ranges(self):
        """Get min/max ranges for each feature"""
        if self.dataset is None:
            raise ValueError("Dataset not loaded. Call load_extended_dataset() first.")
        
        numeric_cols = self.dataset.select_dtypes(include=[np.number]).columns
        
        ranges = {}
        for col in numeric_cols:
            ranges[col] = {
                'min': float(self.dataset[col].min()),
                'max': float(self.dataset[col].max()),
                'mean': float(self.dataset[col].mean()),
                'median': float(self.dataset[col].median())
            }
        
        return ranges
    
    def filter_by_conditions(self, conditions):
        """Filter dataset by specific conditions"""
        if self.dataset is None:
            raise ValueError("Dataset not loaded. Call load_extended_dataset() first.")
        
        filtered = self.dataset.copy()
        
        for column, (min_val, max_val) in conditions.items():
            if column in filtered.columns:
                filtered = filtered[
                    (filtered[column] >= min_val) & 
                    (filtered[column] <= max_val)
                ]
        
        return filtered
    
    def get_water_sensitivity_distribution(self):
        """Get distribution of water sensitivity levels"""
        if self.dataset is None:
            raise ValueError("Dataset not loaded. Call load_extended_dataset() first.")
        
        if 'Water_Sensitivity' in self.dataset.columns:
            distribution = self.dataset['Water_Sensitivity'].value_counts().to_dict()
            return distribution
        else:
            return None


def preprocess_input(input_data, defaults=None):
    """
    Preprocess user input with defaults and validation
    
    Args:
        input_data (dict): User input values
        defaults (dict): Default values for missing inputs
    
    Returns:
        dict: Processed input data
    """
    if defaults is None:
        defaults = {
            'soil_moisture': 50.0,
            'Moisture_Trend': 0.0,
            'Precipitation': 0.0,
            'weather_humidity': 50.0,
            'MaxT': 35.0,
            'MinT': 22.0,
            'Water_Sensitivity': 1,
            'soil_temperature': 25.0,
            'weather_temperature': 28.0
        }
    
    processed = {}
    
    # Fill in missing values with defaults
    for key, default_value in defaults.items():
        if key in input_data and input_data[key] is not None:
            try:
                processed[key] = float(input_data[key])
            except (ValueError, TypeError):
                processed[key] = default_value
        else:
            processed[key] = default_value
    
    # Validate temperature relationship
    if processed['MinT'] > processed['MaxT']:
        processed['MinT'] = processed['MaxT']
    
    return processed


def calculate_irrigation_score(soil_moisture, precipitation, water_sensitivity):
    """
    Calculate a simple irrigation necessity score
    
    Args:
        soil_moisture (float): Current soil moisture %
        precipitation (float): Expected rainfall in mm
        water_sensitivity (int): Crop water sensitivity (0=low, 1=med, 2=high)
    
    Returns:
        float: Irrigation score (0-100, higher = more needed)
    """
    # Base score from soil moisture (inverted - lower moisture = higher score)
    moisture_score = max(0, (65 - soil_moisture) / 65 * 100)
    
    # Reduce score based on expected rainfall
    rain_factor = max(0, 1 - (precipitation / 10))
    
    # Adjust for water sensitivity
    sensitivity_multiplier = 1 + (water_sensitivity * 0.2)
    
    # Calculate final score
    score = moisture_score * rain_factor * sensitivity_multiplier
    
    return min(100, score)


def get_recommendation_text(irrigate, alert):
    """
    Generate recommendation text based on predictions
    
    Args:
        irrigate (int): Irrigation prediction (0 or 1)
        alert (int): Alert prediction (0 or 1)
    
    Returns:
        str: Recommendation text
    """
    recommendations = []
    
    if irrigate == 1:
        recommendations.append("🌊 Irrigation is recommended")
        if alert == 1:
            recommendations.append("⚠️ Monitor soil conditions closely")
    else:
        recommendations.append("✅ No irrigation needed currently")
        if alert == 1:
            recommendations.append("⚠️ However, unusual conditions detected - check sensors")
    
    return " | ".join(recommendations)


# ============================================
# EXAMPLE USAGE
# ============================================
if __name__ == '__main__':
    print("="*60)
    print("DATA LOADER UTILITIES - TEST")
    print("="*60)
    
    # Initialize loader
    loader = DataLoader()
    
    # Load dataset
    try:
        df = loader.load_extended_dataset()
        print(f"\n✓ Dataset loaded successfully")
        print(f"  Columns: {df.columns.tolist()}")
        
        # Get feature ranges
        ranges = loader.get_feature_ranges()
        print(f"\n📊 Feature Ranges:")
        for feature, range_info in list(ranges.items())[:5]:
            print(f"  {feature:25s} {range_info['min']:.2f} - {range_info['max']:.2f}")
        
        # Get water sensitivity distribution
        ws_dist = loader.get_water_sensitivity_distribution()
        if ws_dist:
            print(f"\n💧 Water Sensitivity Distribution:")
            for level, count in ws_dist.items():
                print(f"  Level {int(level)}: {count:,} records")
        
        # Test preprocessing
        print(f"\n🔧 Testing input preprocessing:")
        test_input = {
            'soil_moisture': 45.0,
            'Precipitation': 2.5
        }
        processed = preprocess_input(test_input)
        print(f"  Input: {test_input}")
        print(f"  Processed: {processed}")
        
        # Test irrigation score
        score = calculate_irrigation_score(45, 2.5, 1)
        print(f"\n📈 Irrigation Score: {score:.1f}/100")
        
        print(f"\n✅ All tests passed!")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("Make sure the dataset is in the data/ folder")
    
    print("="*60)
