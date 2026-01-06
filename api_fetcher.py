"""
API Fetcher Module - Automatic Data Collection
===============================================
Fetches real-time agricultural and weather data from multiple APIs
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
import json
from config import (
    AGROMONITORING_API_KEY, AGROMONITORING_BASE_URL,
    OPEN_METEO_BASE_URL, IMD_BASE_URL,
    REQUEST_TIMEOUT
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIFetcher:
    """Handles all external API calls for real-time data"""
    
    def __init__(self):
        self.timeout = REQUEST_TIMEOUT
        self.session = requests.Session()
    
    # ==========================================
    # AGROMONITORING API (Soil Data)
    # ==========================================
    
    def create_polygon(self, name: str, coordinates: List[List[float]]) -> Optional[str]:
        """
        Create a polygon for AgroMonitoring API
        coordinates: [[lon, lat], [lon, lat], ...]
        """
        try:
            url = f"{AGROMONITORING_BASE_URL}/polygons"
            params = {'appid': AGROMONITORING_API_KEY}
            
            data = {
                "name": name,
                "geo_json": {
                    "type": "Feature",
                    "properties": {},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [coordinates]
                    }
                }
            }
            
            response = self.session.post(url, json=data, params=params, timeout=self.timeout)
            
            if response.status_code == 201:
                result = response.json()
                polygon_id = result.get('id')
                logger.info(f"✅ Created polygon: {polygon_id}")
                return polygon_id
            else:
                logger.error(f"Failed to create polygon: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating polygon: {e}")
            return None
    
    def fetch_soil_data(self, polygon_id: str) -> Optional[Dict]:
        """
        Fetch soil moisture and temperature from AgroMonitoring
        Returns: {'soil_moisture': float, 'soil_temp': float}
        """
        try:
            url = f"{AGROMONITORING_BASE_URL}/soil"
            params = {
                'polyid': polygon_id,
                'appid': AGROMONITORING_API_KEY
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract soil moisture (in m³/m³, convert to percentage)
                soil_moisture = data.get('moisture', 0.5) * 100  # Convert to %
                
                # Extract soil temperature (Kelvin to Celsius)
                soil_temp_k = data.get('t10', 288)  # t10 = temperature at 10cm depth
                soil_temp = soil_temp_k - 273.15
                
                logger.info(f"✅ Soil data: moisture={soil_moisture:.1f}%, temp={soil_temp:.1f}°C")
                
                return {
                    'soil_moisture': round(soil_moisture, 1),
                    'soil_temp': round(soil_temp, 1)
                }
            else:
                logger.warning(f"Soil data request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching soil data: {e}")
            return None
    
    # ==========================================
    # OPEN-METEO API (Weather Data)
    # ==========================================
    
    def fetch_weather_data(self, latitude: float, longitude: float) -> Optional[Dict]:
        """
        Fetch weather data from Open-Meteo (free, no API key needed)
        Returns: {
            'Precipitation': float,
            'weather_humidity': float,
            'MaxT': float,
            'MinT': float
        }
        """
        try:
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum',
                'current': 'relative_humidity_2m',
                'timezone': 'auto',
                'forecast_days': 3
            }
            
            response = self.session.get(OPEN_METEO_BASE_URL, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                # Current humidity
                humidity = data.get('current', {}).get('relative_humidity_2m', 50)
                
                # Today's forecast
                daily = data.get('daily', {})
                max_temp = daily.get('temperature_2m_max', [30])[0]
                min_temp = daily.get('temperature_2m_min', [20])[0]
                precipitation = daily.get('precipitation_sum', [0])[0]
                
                logger.info(f"✅ Weather: MaxT={max_temp}°C, MinT={min_temp}°C, Rain={precipitation}mm, Humidity={humidity}%")
                
                return {
                    'Precipitation': round(precipitation, 1),
                    'weather_humidity': int(humidity),
                    'MaxT': round(max_temp, 1),
                    'MinT': round(min_temp, 1)
                }
            else:
                logger.warning(f"Weather data request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return None
    
    # ==========================================
    # IMD API (India Meteorological Department)
    # ==========================================
    
    def fetch_imd_data(self, latitude: float, longitude: float) -> Optional[Dict]:
        """
        Fetch data from India Meteorological Department
        Note: IMD API may require authentication or have limited public access
        This is a placeholder implementation
        """
        try:
            # IMD API structure may vary - this is a generic implementation
            # You may need to adjust based on actual IMD API documentation
            
            url = f"{IMD_BASE_URL}/forecast"
            params = {
                'lat': latitude,
                'lon': longitude
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract relevant data (structure depends on actual API)
                precipitation = data.get('precipitation', 0)
                max_temp = data.get('max_temperature', 30)
                min_temp = data.get('min_temperature', 20)
                humidity = data.get('humidity', 50)
                
                logger.info(f"✅ IMD data fetched successfully")
                
                return {
                    'Precipitation': precipitation,
                    'weather_humidity': humidity,
                    'MaxT': max_temp,
                    'MinT': min_temp
                }
            else:
                logger.warning(f"IMD API not available, using fallback")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching IMD data: {e}")
            return None
    
    # ==========================================
    # HISTORICAL DATA FOR TRENDS
    # ==========================================
    
    def fetch_historical_soil_moisture(self, polygon_id: str, days: int = 7) -> Optional[List[float]]:
        """
        Fetch historical soil moisture data for trend calculation
        """
        try:
            url = f"{AGROMONITORING_BASE_URL}/soil/history"
            
            end_date = int(datetime.now().timestamp())
            start_date = int((datetime.now() - timedelta(days=days)).timestamp())
            
            params = {
                'polyid': polygon_id,
                'appid': AGROMONITORING_API_KEY,
                'start': start_date,
                'end': end_date
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract moisture values
                moisture_values = []
                for item in data:
                    moisture = item.get('moisture', 0.5) * 100
                    moisture_values.append(moisture)
                
                logger.info(f"✅ Historical data: {len(moisture_values)} records")
                return moisture_values
            else:
                logger.warning(f"Historical data request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return None
    
    def calculate_moisture_trend(self, moisture_history: List[float]) -> float:
        """
        Calculate moisture trend from historical data
        Returns: trend value (negative = drying, positive = wetting)
        """
        if not moisture_history or len(moisture_history) < 2:
            return 0.0
        
        # Simple linear regression slope
        n = len(moisture_history)
        x = list(range(n))
        y = moisture_history
        
        # Calculate slope (trend)
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        
        logger.info(f"✅ Moisture trend: {slope:.2f}")
        return round(slope, 2)


# ==========================================
# FALLBACK DATA GENERATOR
# ==========================================

def generate_fallback_data(latitude: float, longitude: float) -> Dict:
    """
    Generate reasonable fallback data when APIs are unavailable
    Based on location and season
    """
    # Determine season based on month
    month = datetime.now().month
    
    # India: Summer (Mar-Jun), Monsoon (Jul-Sep), Winter (Oct-Feb)
    if 3 <= month <= 6:  # Summer
        return {
            'soil_moisture': 45.0,
            'soil_temp': 28.0,
            'Precipitation': 0.5,
            'weather_humidity': 35,
            'MaxT': 38.0,
            'MinT': 26.0,
            'Moisture_Trend': -1.5
        }
    elif 7 <= month <= 9:  # Monsoon
        return {
            'soil_moisture': 58.0,
            'soil_temp': 24.0,
            'Precipitation': 8.0,
            'weather_humidity': 80,
            'MaxT': 30.0,
            'MinT': 22.0,
            'Moisture_Trend': 2.0
        }
    else:  # Winter
        return {
            'soil_moisture': 52.0,
            'soil_temp': 18.0,
            'Precipitation': 1.0,
            'weather_humidity': 55,
            'MaxT': 28.0,
            'MinT': 16.0,
            'Moisture_Trend': -0.5
        }


# ==========================================
# TESTING FUNCTION
# ==========================================

if __name__ == "__main__":
    print("Testing API Fetcher...")
    
    # Test coordinates (example: Delhi, India)
    test_lat = 28.6139
    test_lon = 77.2090
    
    fetcher = APIFetcher()
    
    # Test weather data
    print("\n--- Testing Open-Meteo Weather API ---")
    weather = fetcher.fetch_weather_data(test_lat, test_lon)
    print(f"Weather data: {weather}")
    
    # Test fallback
    print("\n--- Testing Fallback Data ---")
    fallback = generate_fallback_data(test_lat, test_lon)
    print(f"Fallback data: {fallback}")
