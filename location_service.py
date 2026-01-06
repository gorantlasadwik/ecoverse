"""
Location Service - Automatic Data Fetching Based on Location
=============================================================
Coordinates all API calls and provides unified data interface
"""

import logging
from typing import Dict, Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from api_fetcher import APIFetcher, generate_fallback_data
from config import GEOCODING_USER_AGENT, CROP_WATER_SENSITIVITY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocationService:
    """Handles location-based automatic data fetching"""
    
    def __init__(self):
        self.api_fetcher = APIFetcher()
        self.geocoder = Nominatim(user_agent=GEOCODING_USER_AGENT)
        self.polygon_cache = {}  # Cache polygon IDs for locations
    
    def geocode_location(self, location_name: str) -> Optional[Tuple[float, float]]:
        """
        Convert location name to coordinates
        Returns: (latitude, longitude) or None
        """
        try:
            location = self.geocoder.geocode(location_name, timeout=10)
            
            if location:
                logger.info(f"✅ Geocoded '{location_name}' to ({location.latitude}, {location.longitude})")
                return (location.latitude, location.longitude)
            else:
                logger.warning(f"Could not geocode location: {location_name}")
                return None
                
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Geocoding error: {e}")
            return None
    
    def create_field_polygon(self, center_lat: float, center_lon: float, size_km: float = 0.5) -> list:
        """
        Create a square polygon around the center point
        size_km: size of the field in kilometers
        Returns: list of [lon, lat] coordinates
        """
        # Approximate degree conversion (1 degree ≈ 111 km)
        offset = size_km / 111.0 / 2
        
        # Create square polygon
        polygon = [
            [center_lon - offset, center_lat + offset],  # Top-left
            [center_lon + offset, center_lat + offset],  # Top-right
            [center_lon + offset, center_lat - offset],  # Bottom-right
            [center_lon - offset, center_lat - offset],  # Bottom-left
            [center_lon - offset, center_lat + offset]   # Close polygon
        ]
        
        return polygon
    
    def get_or_create_polygon_id(self, location_name: str, lat: float, lon: float) -> Optional[str]:
        """
        Get existing polygon ID or create new one for the location
        """
        # Check cache
        cache_key = f"{lat:.4f},{lon:.4f}"
        if cache_key in self.polygon_cache:
            logger.info(f"Using cached polygon ID for {location_name}")
            return self.polygon_cache[cache_key]
        
        # Create new polygon
        polygon_coords = self.create_field_polygon(lat, lon)
        polygon_id = self.api_fetcher.create_polygon(location_name, polygon_coords)
        
        if polygon_id:
            self.polygon_cache[cache_key] = polygon_id
            logger.info(f"✅ Created and cached polygon ID: {polygon_id}")
        
        return polygon_id
    
    def fetch_all_data_by_coordinates(self, latitude: float, longitude: float, 
                                      crop_type: str = 'wheat', location_name: str = "Field") -> Dict:
        """
        Fetch all required data for ML model based on coordinates
        
        Args:
            latitude: Field latitude
            longitude: Field longitude
            crop_type: Type of crop for water sensitivity
            location_name: Name of the field/location
        
        Returns:
            Complete data dictionary ready for ML model
        """
        logger.info(f"🌍 Fetching data for location: {location_name} ({latitude}, {longitude})")
        
        result = {
            'location': location_name,
            'coordinates': {'latitude': latitude, 'longitude': longitude},
            'data_sources': {},
            'success': True
        }
        
        # 1. Fetch Weather Data (Open-Meteo) - High priority, most reliable
        weather_data = self.api_fetcher.fetch_weather_data(latitude, longitude)
        
        if weather_data:
            result['Precipitation'] = weather_data['Precipitation']
            result['weather_humidity'] = weather_data['weather_humidity']
            result['MaxT'] = weather_data['MaxT']
            result['MinT'] = weather_data['MinT']
            result['data_sources']['weather'] = 'Open-Meteo'
            logger.info("✅ Weather data fetched from Open-Meteo")
        else:
            logger.warning("⚠️ Weather API failed, using fallback")
            fallback = generate_fallback_data(latitude, longitude)
            result['Precipitation'] = fallback['Precipitation']
            result['weather_humidity'] = fallback['weather_humidity']
            result['MaxT'] = fallback['MaxT']
            result['MinT'] = fallback['MinT']
            result['data_sources']['weather'] = 'Fallback (seasonal)'
        
        # 2. Fetch Soil Data (AgroMonitoring) - Requires polygon setup
        try:
            polygon_id = self.get_or_create_polygon_id(location_name, latitude, longitude)
            
            if polygon_id:
                soil_data = self.api_fetcher.fetch_soil_data(polygon_id)
                
                if soil_data:
                    result['soil_moisture'] = soil_data['soil_moisture']
                    result['soil_temp'] = soil_data['soil_temp']
                    result['data_sources']['soil'] = 'AgroMonitoring'
                    logger.info("✅ Soil data fetched from AgroMonitoring")
                    
                    # 3. Fetch Historical Data for Moisture Trend
                    moisture_history = self.api_fetcher.fetch_historical_soil_moisture(polygon_id, days=7)
                    
                    if moisture_history:
                        result['Moisture_Trend'] = self.api_fetcher.calculate_moisture_trend(moisture_history)
                        result['data_sources']['trend'] = 'AgroMonitoring (7-day history)'
                        logger.info(f"✅ Moisture trend calculated: {result['Moisture_Trend']}")
                    else:
                        result['Moisture_Trend'] = 0.0
                        result['data_sources']['trend'] = 'Default (no history)'
                        logger.warning("⚠️ Could not calculate trend, using default")
                else:
                    raise Exception("Soil data fetch failed")
            else:
                raise Exception("Polygon creation failed")
                
        except Exception as e:
            logger.warning(f"⚠️ Soil data unavailable: {e}. Using fallback.")
            fallback = generate_fallback_data(latitude, longitude)
            result['soil_moisture'] = fallback['soil_moisture']
            result['soil_temp'] = fallback['soil_temp']
            result['Moisture_Trend'] = fallback['Moisture_Trend']
            result['data_sources']['soil'] = 'Fallback (seasonal)'
            result['data_sources']['trend'] = 'Fallback (seasonal)'
        
        # 4. Crop Water Sensitivity (Static lookup)
        crop_type_lower = crop_type.lower().replace(' ', '_')
        result['Water_Sensitivity'] = CROP_WATER_SENSITIVITY.get(crop_type_lower, 1)
        result['crop_type'] = crop_type
        result['data_sources']['sensitivity'] = 'FAO/ICAR lookup table'
        logger.info(f"✅ Water sensitivity for {crop_type}: {result['Water_Sensitivity']}")
        
        # 5. Field Status (will be determined by ML model)
        result['field_status'] = 'normal'  # Default, ML will override
        result['data_sources']['field_status'] = 'Default (pre-inference)'
        
        # Log summary
        logger.info("=" * 60)
        logger.info("📊 DATA COLLECTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Location: {location_name}")
        logger.info(f"Coordinates: {latitude}, {longitude}")
        logger.info(f"Crop: {crop_type} (sensitivity: {result['Water_Sensitivity']})")
        logger.info(f"Soil Moisture: {result['soil_moisture']:.1f}% (source: {result['data_sources']['soil']})")
        logger.info(f"Temperature: {result['MinT']:.1f}°C - {result['MaxT']:.1f}°C")
        logger.info(f"Precipitation: {result['Precipitation']:.1f}mm")
        logger.info(f"Humidity: {result['weather_humidity']}%")
        logger.info(f"Moisture Trend: {result['Moisture_Trend']:.1f}")
        logger.info("=" * 60)
        
        return result
    
    def fetch_all_data_by_location_name(self, location_name: str, crop_type: str = 'wheat') -> Optional[Dict]:
        """
        Fetch all data by location name (geocodes first, then fetches data)
        
        Args:
            location_name: Name of location (e.g., "Delhi, India" or "Pune, Maharashtra")
            crop_type: Type of crop
        
        Returns:
            Complete data dictionary or None if geocoding fails
        """
        # Geocode location
        coords = self.geocode_location(location_name)
        
        if not coords:
            logger.error(f"❌ Could not geocode location: {location_name}")
            return None
        
        latitude, longitude = coords
        
        # Fetch all data
        return self.fetch_all_data_by_coordinates(latitude, longitude, crop_type, location_name)
    
    def get_ml_ready_input(self, location_data: Dict) -> Dict:
        """
        Extract ML model input from location data
        Returns only the fields needed by the ML model
        """
        return {
            'soil_moisture': location_data['soil_moisture'],
            'Moisture_Trend': location_data['Moisture_Trend'],
            'Precipitation': location_data['Precipitation'],
            'weather_humidity': location_data['weather_humidity'],
            'MaxT': location_data['MaxT'],
            'MinT': location_data['MinT'],
            'Water_Sensitivity': location_data['Water_Sensitivity']
        }


# ==========================================
# TESTING FUNCTION
# ==========================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTING LOCATION SERVICE")
    print("=" * 60)
    
    service = LocationService()
    
    # Test 1: Fetch by coordinates
    print("\n--- Test 1: Fetch by Coordinates (Delhi) ---")
    data = service.fetch_all_data_by_coordinates(28.6139, 77.2090, crop_type='wheat', location_name='Delhi Farm')
    print(f"\nML-ready input: {service.get_ml_ready_input(data)}")
    
    # Test 2: Fetch by location name
    print("\n--- Test 2: Fetch by Location Name (Pune, India) ---")
    data2 = service.fetch_all_data_by_location_name('Pune, Maharashtra, India', crop_type='rice')
    if data2:
        print(f"\nML-ready input: {service.get_ml_ready_input(data2)}")
    
    print("\n" + "=" * 60)
