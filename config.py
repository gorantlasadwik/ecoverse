"""
Configuration file for API keys and settings
============================================
Store your API keys here. For production, use environment variables.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys (Get from respective providers)
AGROMONITORING_API_KEY = os.getenv('AGROMONITORING_API_KEY', '557020a78e8f06b933bde0490e745ef2')  # Get from: https://agromonitoring.com/api
NASA_EARTHDATA_TOKEN = os.getenv('NASA_EARTHDATA_TOKEN', '')  # Get from: https://urs.earthdata.nasa.gov/
IMD_API_KEY = os.getenv('IMD_API_KEY', '')  # India Meteorological Department

# API Base URLs
AGROMONITORING_BASE_URL = "https://api.agromonitoring.com/agro/1.0"
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
IMD_BASE_URL = "https://mausam.imd.gov.in/api"
NASA_SMAP_BASE_URL = "https://earthdata.nasa.gov/smap"

# Default settings
DEFAULT_POLYGON_ID = None  # Will be created dynamically based on location
CACHE_DURATION_HOURS = 6  # Cache API responses for 6 hours
REQUEST_TIMEOUT = 10  # seconds

# Crop sensitivity mapping (FAO/ICAR based)
CROP_WATER_SENSITIVITY = {
    # High sensitivity crops (2)
    'tomato': 2, 'cucumber': 2, 'lettuce': 2, 'strawberry': 2,
    'banana': 2, 'sugarcane': 2, 'rice': 2, 'potato': 2,
    
    # Medium sensitivity crops (1)
    'wheat': 1, 'maize': 1, 'cotton': 1, 'soybean': 1,
    'onion': 1, 'carrot': 1, 'cabbage': 1, 'sunflower': 1,
    
    # Low sensitivity crops (0)
    'sorghum': 0, 'millet': 0, 'chickpea': 0, 'groundnut': 0,
    'sesame': 0, 'barley': 0, 'cowpea': 0, 'pigeon_pea': 0
}

# Location geocoding settings
GEOCODING_PROVIDER = "nominatim"  # Free OpenStreetMap geocoding
GEOCODING_USER_AGENT = "smart-irrigation-app"
