"""
Crop Sensitivity Database
==========================
FAO and ICAR based crop water sensitivity classifications
"""

# Comprehensive crop database with water sensitivity and characteristics
CROP_DATABASE = {
    # HIGH SENSITIVITY CROPS (Water_Sensitivity = 2)
    # These crops need frequent irrigation and are sensitive to water stress
    'rice': {
        'sensitivity': 2,
        'name': 'Rice (Paddy)',
        'water_requirement': 'Very High',
        'critical_stages': ['Flowering', 'Grain filling'],
        'optimal_moisture': '55-65%',
        'category': 'Cereal'
    },
    'sugarcane': {
        'sensitivity': 2,
        'name': 'Sugarcane',
        'water_requirement': 'Very High',
        'critical_stages': ['Germination', 'Tillering', 'Grand growth'],
        'optimal_moisture': '60-70%',
        'category': 'Cash Crop'
    },
    'banana': {
        'sensitivity': 2,
        'name': 'Banana',
        'water_requirement': 'Very High',
        'critical_stages': ['Vegetative growth', 'Fruit development'],
        'optimal_moisture': '55-65%',
        'category': 'Fruit'
    },
    'tomato': {
        'sensitivity': 2,
        'name': 'Tomato',
        'water_requirement': 'High',
        'critical_stages': ['Flowering', 'Fruit setting'],
        'optimal_moisture': '50-60%',
        'category': 'Vegetable'
    },
    'potato': {
        'sensitivity': 2,
        'name': 'Potato',
        'water_requirement': 'High',
        'critical_stages': ['Tuber initiation', 'Tuber bulking'],
        'optimal_moisture': '50-60%',
        'category': 'Vegetable'
    },
    'cucumber': {
        'sensitivity': 2,
        'name': 'Cucumber',
        'water_requirement': 'High',
        'critical_stages': ['Flowering', 'Fruit development'],
        'optimal_moisture': '55-65%',
        'category': 'Vegetable'
    },
    'lettuce': {
        'sensitivity': 2,
        'name': 'Lettuce',
        'water_requirement': 'High',
        'critical_stages': ['Head formation'],
        'optimal_moisture': '55-65%',
        'category': 'Leafy Vegetable'
    },
    'strawberry': {
        'sensitivity': 2,
        'name': 'Strawberry',
        'water_requirement': 'High',
        'critical_stages': ['Flowering', 'Fruit development'],
        'optimal_moisture': '50-60%',
        'category': 'Fruit'
    },
    'cabbage': {
        'sensitivity': 2,
        'name': 'Cabbage',
        'water_requirement': 'High',
        'critical_stages': ['Head formation'],
        'optimal_moisture': '50-60%',
        'category': 'Vegetable'
    },
    'cauliflower': {
        'sensitivity': 2,
        'name': 'Cauliflower',
        'water_requirement': 'High',
        'critical_stages': ['Curd formation'],
        'optimal_moisture': '50-60%',
        'category': 'Vegetable'
    },
    
    # MEDIUM SENSITIVITY CROPS (Water_Sensitivity = 1)
    # These crops can tolerate moderate water stress
    'wheat': {
        'sensitivity': 1,
        'name': 'Wheat',
        'water_requirement': 'Medium',
        'critical_stages': ['Crown root initiation', 'Flowering', 'Grain filling'],
        'optimal_moisture': '45-55%',
        'category': 'Cereal'
    },
    'maize': {
        'sensitivity': 1,
        'name': 'Maize (Corn)',
        'water_requirement': 'Medium',
        'critical_stages': ['Flowering', 'Grain filling'],
        'optimal_moisture': '45-55%',
        'category': 'Cereal'
    },
    'cotton': {
        'sensitivity': 1,
        'name': 'Cotton',
        'water_requirement': 'Medium',
        'critical_stages': ['Flowering', 'Boll development'],
        'optimal_moisture': '45-55%',
        'category': 'Cash Crop'
    },
    'soybean': {
        'sensitivity': 1,
        'name': 'Soybean',
        'water_requirement': 'Medium',
        'critical_stages': ['Flowering', 'Pod filling'],
        'optimal_moisture': '45-55%',
        'category': 'Legume'
    },
    'sunflower': {
        'sensitivity': 1,
        'name': 'Sunflower',
        'water_requirement': 'Medium',
        'critical_stages': ['Flowering', 'Seed filling'],
        'optimal_moisture': '45-55%',
        'category': 'Oilseed'
    },
    'onion': {
        'sensitivity': 1,
        'name': 'Onion',
        'water_requirement': 'Medium',
        'critical_stages': ['Bulb development'],
        'optimal_moisture': '45-55%',
        'category': 'Vegetable'
    },
    'carrot': {
        'sensitivity': 1,
        'name': 'Carrot',
        'water_requirement': 'Medium',
        'critical_stages': ['Root development'],
        'optimal_moisture': '45-55%',
        'category': 'Vegetable'
    },
    'pea': {
        'sensitivity': 1,
        'name': 'Pea',
        'water_requirement': 'Medium',
        'critical_stages': ['Flowering', 'Pod filling'],
        'optimal_moisture': '45-55%',
        'category': 'Legume'
    },
    'mustard': {
        'sensitivity': 1,
        'name': 'Mustard',
        'water_requirement': 'Medium',
        'critical_stages': ['Flowering', 'Seed filling'],
        'optimal_moisture': '45-55%',
        'category': 'Oilseed'
    },
    'barley': {
        'sensitivity': 1,
        'name': 'Barley',
        'water_requirement': 'Medium',
        'critical_stages': ['Tillering', 'Grain filling'],
        'optimal_moisture': '45-55%',
        'category': 'Cereal'
    },
    
    # LOW SENSITIVITY CROPS (Water_Sensitivity = 0)
    # These crops are drought-tolerant and can withstand water stress
    'sorghum': {
        'sensitivity': 0,
        'name': 'Sorghum (Jowar)',
        'water_requirement': 'Low',
        'critical_stages': ['Flowering'],
        'optimal_moisture': '40-50%',
        'category': 'Cereal'
    },
    'millet': {
        'sensitivity': 0,
        'name': 'Pearl Millet (Bajra)',
        'water_requirement': 'Low',
        'critical_stages': ['Flowering'],
        'optimal_moisture': '40-50%',
        'category': 'Cereal'
    },
    'chickpea': {
        'sensitivity': 0,
        'name': 'Chickpea (Chana)',
        'water_requirement': 'Low',
        'critical_stages': ['Flowering', 'Pod development'],
        'optimal_moisture': '40-50%',
        'category': 'Legume'
    },
    'groundnut': {
        'sensitivity': 0,
        'name': 'Groundnut (Peanut)',
        'water_requirement': 'Low',
        'critical_stages': ['Flowering', 'Pegging'],
        'optimal_moisture': '40-50%',
        'category': 'Oilseed'
    },
    'pigeon_pea': {
        'sensitivity': 0,
        'name': 'Pigeon Pea (Tur/Arhar)',
        'water_requirement': 'Low',
        'critical_stages': ['Flowering', 'Pod filling'],
        'optimal_moisture': '40-50%',
        'category': 'Legume'
    },
    'cowpea': {
        'sensitivity': 0,
        'name': 'Cowpea',
        'water_requirement': 'Low',
        'critical_stages': ['Flowering', 'Pod filling'],
        'optimal_moisture': '40-50%',
        'category': 'Legume'
    },
    'sesame': {
        'sensitivity': 0,
        'name': 'Sesame (Til)',
        'water_requirement': 'Low',
        'critical_stages': ['Flowering', 'Capsule formation'],
        'optimal_moisture': '40-50%',
        'category': 'Oilseed'
    },
    'safflower': {
        'sensitivity': 0,
        'name': 'Safflower',
        'water_requirement': 'Low',
        'critical_stages': ['Flowering'],
        'optimal_moisture': '40-50%',
        'category': 'Oilseed'
    },
    'green_gram': {
        'sensitivity': 0,
        'name': 'Green Gram (Moong)',
        'water_requirement': 'Low',
        'critical_stages': ['Flowering', 'Pod filling'],
        'optimal_moisture': '40-50%',
        'category': 'Legume'
    },
    'black_gram': {
        'sensitivity': 0,
        'name': 'Black Gram (Urad)',
        'water_requirement': 'Low',
        'critical_stages': ['Flowering', 'Pod filling'],
        'optimal_moisture': '40-50%',
        'category': 'Legume'
    }
}


def get_crop_sensitivity(crop_name: str) -> int:
    """
    Get water sensitivity value for a crop
    Returns: 0 (Low), 1 (Medium), or 2 (High)
    """
    crop_key = crop_name.lower().replace(' ', '_').replace('-', '_')
    
    if crop_key in CROP_DATABASE:
        return CROP_DATABASE[crop_key]['sensitivity']
    
    # Default to medium sensitivity if crop not found
    return 1


def get_crop_info(crop_name: str) -> dict:
    """
    Get complete information about a crop
    """
    crop_key = crop_name.lower().replace(' ', '_').replace('-', '_')
    
    if crop_key in CROP_DATABASE:
        return CROP_DATABASE[crop_key]
    
    # Return default info for unknown crops
    return {
        'sensitivity': 1,
        'name': crop_name,
        'water_requirement': 'Medium',
        'critical_stages': ['Growth period'],
        'optimal_moisture': '45-55%',
        'category': 'Unknown'
    }


def get_all_crops_by_sensitivity(sensitivity: int) -> list:
    """
    Get list of all crops with given sensitivity level
    """
    return [
        {
            'key': key,
            'name': data['name'],
            'category': data['category']
        }
        for key, data in CROP_DATABASE.items()
        if data['sensitivity'] == sensitivity
    ]


def search_crops(query: str) -> list:
    """
    Search for crops by name
    """
    query_lower = query.lower()
    results = []
    
    for key, data in CROP_DATABASE.items():
        if query_lower in key or query_lower in data['name'].lower():
            results.append({
                'key': key,
                'name': data['name'],
                'sensitivity': data['sensitivity'],
                'category': data['category']
            })
    
    return results


# Export simple mapping for backward compatibility
CROP_WATER_SENSITIVITY = {
    key: data['sensitivity'] 
    for key, data in CROP_DATABASE.items()
}


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CROP SENSITIVITY DATABASE")
    print("="*60)
    
    # Test sensitivity lookup
    print("\n--- Water Sensitivity Lookup ---")
    test_crops = ['rice', 'wheat', 'sorghum', 'unknown_crop']
    for crop in test_crops:
        sensitivity = get_crop_sensitivity(crop)
        info = get_crop_info(crop)
        print(f"{info['name']}: Sensitivity={sensitivity}, Water Requirement={info['water_requirement']}")
    
    # List crops by sensitivity
    print("\n--- High Sensitivity Crops (2) ---")
    high_sens = get_all_crops_by_sensitivity(2)
    for crop in high_sens[:5]:
        print(f"  - {crop['name']} ({crop['category']})")
    print(f"  ... and {len(high_sens) - 5} more")
    
    print("\n--- Medium Sensitivity Crops (1) ---")
    med_sens = get_all_crops_by_sensitivity(1)
    for crop in med_sens[:5]:
        print(f"  - {crop['name']} ({crop['category']})")
    
    print("\n--- Low Sensitivity Crops (0) ---")
    low_sens = get_all_crops_by_sensitivity(0)
    for crop in low_sens[:5]:
        print(f"  - {crop['name']} ({crop['category']})")
    
    # Search test
    print("\n--- Search: 'gram' ---")
    results = search_crops('gram')
    for r in results:
        print(f"  - {r['name']} (sensitivity: {r['sensitivity']})")
    
    print("\n" + "="*60)
