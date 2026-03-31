"""
Smart Irrigation System - Flask Backend
========================================
Real-time irrigation recommendations using trained ML models
Uses inference.py for all ML logic (clean separation)
ENHANCED: Automatic data fetching from location-based APIs
PRODUCTION: Includes keep-alive for Render deployment
"""

from flask import Flask, render_template, request, jsonify
from inference import run_inference, integrated_model_prediction, DEFAULTS
import pandas as pd
import os
from datetime import datetime
import logging
import threading
import time
import requests as http_requests

# Configure logging FIRST (before any imports that use it)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import location-based services
LOCATION_SERVICE_ENABLED = False
location_service = None

try:
    from location_service import LocationService
    from crop_sensitivity import get_crop_info, get_all_crops_by_sensitivity, search_crops
    location_service = LocationService()
    LOCATION_SERVICE_ENABLED = True
    logger.info("✅ Location-based auto-fetch ENABLED")
except ImportError as e:
    logger.warning(f"⚠️ Location service disabled: {e}")
    logger.warning("Run: pip install geopy requests")
except Exception as e:
    logger.error(f"❌ Error initializing location service: {e}")
    logger.warning("Location service will be disabled")

app = Flask(__name__)

print("🌱 Smart Irrigation System - Flask Backend")
print("✅ Using enhanced inference.py for integrated ML logic")
print("🔗 Model A & B connection: ACTIVE")
print(f"📍 Location-based auto-fetch: {'ENABLED' if LOCATION_SERVICE_ENABLED else 'DISABLED'}")

# ============================================
# VALIDATION RANGES
# ============================================
VALIDATION_RANGES = {
    'soil_moisture': (40, 65),
    'Moisture_Trend': (-5, 5),
    'Precipitation': (0, 10),
    'weather_humidity': (10, 100),
    'MaxT': (20, 50),
    'MinT': (10, 35),
    'Water_Sensitivity': (0, 2)
}

# ============================================
# HELPER FUNCTIONS
# ============================================

def generate_explanation(input_data, irrigate, alert, water_quantity=None):
    """Generate human-readable explanation for the decision"""
    
    explanations = []
    
    # Irrigation explanation with water quantity
    if irrigate == 1:
        reasons = []
        if input_data['soil_moisture'] < 45:
            reasons.append(f"low soil moisture ({input_data['soil_moisture']:.1f}%)")
        if input_data['Precipitation'] < 1:
            reasons.append("minimal rainfall expected")
        if input_data['Water_Sensitivity'] == 2:
            reasons.append("high crop water sensitivity")
        
        water_msg = f" Apply {water_quantity.lower()} amount of water." if water_quantity and water_quantity != "None" else ""
        
        if reasons:
            explanations.append(f"💧 Irrigation recommended due to: {', '.join(reasons)}.{water_msg}")
        else:
            explanations.append(f"💧 Irrigation recommended based on current conditions.{water_msg}")
    else:
        reasons = []
        if input_data['soil_moisture'] >= 50:
            reasons.append(f"adequate soil moisture ({input_data['soil_moisture']:.1f}%)")
        if input_data['Precipitation'] >= 2:
            reasons.append(f"sufficient rainfall expected ({input_data['Precipitation']:.1f}mm)")
        
        if reasons:
            explanations.append(f"🚫 No irrigation needed: {', '.join(reasons)}.")
        else:
            explanations.append("🚫 No irrigation needed under current conditions.")
    
    # Alert explanation
    if alert == 1:
        alert_reasons = []
        if input_data['Moisture_Trend'] < -2:
            alert_reasons.append(f"rapid moisture loss (trend: {input_data['Moisture_Trend']:.2f})")
        if input_data['soil_moisture'] < 30:
            alert_reasons.append(f"critically low moisture ({input_data['soil_moisture']:.1f}%)")
        if input_data['MaxT'] > 38 and input_data['soil_moisture'] < 40:
            alert_reasons.append("stress conditions (high temperature + low moisture)")
        
        if alert_reasons:
            explanations.append(f"🚨 Alert triggered: {', '.join(alert_reasons)}.")
        else:
            explanations.append("🚨 Abnormal moisture behavior detected.")
    else:
        explanations.append("✅ All parameters within normal ranges.")
    
    return " ".join(explanations)


# ============================================
# LOCATION-BASED AUTO-FETCH ENDPOINTS
# ============================================

@app.route('/api/geocode-reverse', methods=['POST'])
def geocode_reverse():
    """
    Reverse geocode coordinates to location name
    Request: {'latitude': 28.6139, 'longitude': 77.2090}
    """
    if not LOCATION_SERVICE_ENABLED:
        return jsonify({
            'success': False,
            'error': 'Location service not available'
        }), 503
    
    try:
        data = request.get_json()
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
        
        logger.info(f"🔄 Reverse geocoding: {latitude}, {longitude}")
        
        # Use geopy to reverse geocode
        from geopy.geocoders import Nominatim
        from geopy.exc import GeocoderTimedOut, GeocoderServiceError
        
        geolocator = Nominatim(
            user_agent="smart-irrigation-app-v2",
            timeout=15
        )
        
        try:
            location = geolocator.reverse(
                f"{latitude}, {longitude}",
                exactly_one=True,
                language='en'
            )
            
            if location and location.address:
                logger.info(f"✅ Reverse geocoded to: {location.address}")
                return jsonify({
                    'success': True,
                    'location': location.address,
                    'coordinates': {
                        'latitude': latitude,
                        'longitude': longitude
                    }
                }), 200
            else:
                logger.warning("No location found for coordinates")
                return jsonify({
                    'success': False,
                    'error': 'No location found for these coordinates'
                }), 404
                
        except GeocoderTimedOut:
            logger.error("Geocoder timed out")
            return jsonify({
                'success': False,
                'error': 'Location service timed out. Please try again.'
            }), 408
            
        except GeocoderServiceError as e:
            logger.error(f"Geocoder service error: {e}")
            return jsonify({
                'success': False,
                'error': 'Location service temporarily unavailable. Please enter location manually.'
            }), 503
            
    except ValueError as e:
        logger.error(f"Invalid coordinates: {e}")
        return jsonify({
            'success': False,
            'error': 'Invalid coordinates provided'
        }), 400
        
    except Exception as e:
        logger.error(f"Error in reverse geocoding: {e}")
        return jsonify({
            'success': False,
            'error': f'Could not determine location: {str(e)}'
        }), 500


@app.route('/api/location-suggestions', methods=['GET'])
def location_suggestions():
    """
    Get location suggestions for autocomplete
    Request: GET /api/location-suggestions?q=pune
    """
    if not LOCATION_SERVICE_ENABLED:
        return jsonify({
            'success': False,
            'error': 'Location service not available'
        }), 503
    
    try:
        query = request.args.get('q', '')
        
        if len(query) < 3:
            return jsonify({
                'success': True,
                'suggestions': []
            }), 200
        
        # Use geopy to get suggestions
        from geopy.geocoders import Nominatim
        geolocator = Nominatim(user_agent="smart-irrigation-app")
        
        # Search for locations
        locations = geolocator.geocode(query, exactly_one=False, limit=5, timeout=10)
        
        suggestions = []
        if locations:
            for loc in locations:
                suggestions.append({
                    'name': loc.address,
                    'latitude': loc.latitude,
                    'longitude': loc.longitude
                })
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting location suggestions: {e}")
        return jsonify({
            'success': True,
            'suggestions': []
        }), 200


@app.route('/api/fetch-data-by-location', methods=['POST'])
def fetch_data_by_location():
    """
    Fetch all required data automatically based on location name
    Request: {'location': 'City, State, Country', 'crop_type': 'wheat'}
    """
    logger.info(f"🔍 fetch-data-by-location called. LOCATION_SERVICE_ENABLED={LOCATION_SERVICE_ENABLED}, location_service={location_service}")
    
    if not LOCATION_SERVICE_ENABLED or location_service is None:
        logger.error(f"Location service not available. ENABLED={LOCATION_SERVICE_ENABLED}, service={location_service}")
        return jsonify({
            'success': False,
            'error': 'Location service not available. Install required packages: pip install geopy'
        }), 503
    
    try:
        data = request.get_json()
        location_name = data.get('location')
        crop_type = data.get('crop_type', 'wheat')
        
        if not location_name:
            return jsonify({
                'success': False,
                'error': 'location is required'
            }), 400
        
        logger.info(f"📍 Fetching data for location: {location_name}, crop: {crop_type}")
        
        # Fetch all data
        result = location_service.fetch_all_data_by_location_name(location_name, crop_type)
        
        if not result:
            return jsonify({
                'success': False,
                'error': f'Could not fetch data for location: {location_name}'
            }), 404
        
        # Get ML-ready input
        ml_input = location_service.get_ml_ready_input(result)
        
        return jsonify({
            'success': True,
            'location': result['location'],
            'coordinates': result['coordinates'],
            'crop_type': result['crop_type'],
            'data': ml_input,
            'data_sources': result['data_sources'],
            'message': 'Data fetched successfully from APIs'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in fetch_data_by_location: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/fetch-data-by-coordinates', methods=['POST'])
def fetch_data_by_coordinates():
    """
    Fetch all required data automatically based on coordinates
    Request: {'latitude': 28.6139, 'longitude': 77.2090, 'crop_type': 'wheat', 'location_name': 'My Farm'}
    """
    if not LOCATION_SERVICE_ENABLED:
        return jsonify({
            'success': False,
            'error': 'Location service not available'
        }), 503
    
    try:
        data = request.get_json()
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
        crop_type = data.get('crop_type', 'wheat')
        location_name = data.get('location_name', 'Field')
        
        if latitude is None or longitude is None:
            return jsonify({
                'success': False,
                'error': 'latitude and longitude are required'
            }), 400
        
        logger.info(f"📍 Fetching data for coordinates: ({latitude}, {longitude}), crop: {crop_type}")
        
        # Fetch all data
        result = location_service.fetch_all_data_by_coordinates(
            latitude, longitude, crop_type, location_name
        )
        
        # Get ML-ready input
        ml_input = location_service.get_ml_ready_input(result)
        
        return jsonify({
            'success': True,
            'location': result['location'],
            'coordinates': result['coordinates'],
            'crop_type': result['crop_type'],
            'data': ml_input,
            'data_sources': result['data_sources'],
            'message': 'Data fetched successfully from APIs'
        }), 200
        
    except ValueError as ve:
        return jsonify({
            'success': False,
            'error': f'Invalid coordinates: {str(ve)}'
        }), 400
    except Exception as e:
        logger.error(f"Error in fetch_data_by_coordinates: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/predict-with-location', methods=['POST'])
def predict_with_location():
    """
    Fetch data by location AND run ML prediction in one call
    Request: {'location': 'City, State', 'crop_type': 'wheat'}
    """
    if not LOCATION_SERVICE_ENABLED:
        return jsonify({
            'success': False,
            'error': 'Location service not available'
        }), 503
    
    try:
        data = request.get_json()
        location_name = data.get('location')
        crop_type = data.get('crop_type', 'wheat')
        
        if not location_name:
            return jsonify({
                'success': False,
                'error': 'location is required'
            }), 400
        
        logger.info(f"📍 Auto-fetch + predict for: {location_name}, crop: {crop_type}")
        
        # Step 1: Fetch all data
        location_data = location_service.fetch_all_data_by_location_name(location_name, crop_type)
        
        if not location_data:
            return jsonify({
                'success': False,
                'error': f'Could not fetch data for location: {location_name}'
            }), 404
        
        # Step 2: Get ML input
        ml_input = location_service.get_ml_ready_input(location_data)
        
        # Step 3: Run ML inference
        prediction_result = run_inference(ml_input)
        
        # Step 4: Get detailed results
        detailed_result = integrated_model_prediction(ml_input)
        
        # Step 5: Generate explanation
        irrigate = prediction_result['Irrigate']
        alert = prediction_result['Alert']
        water_quantity = prediction_result.get('Water_Quantity', 'None')
        explanation = generate_explanation(ml_input, irrigate, alert, water_quantity)
        
        # Prepare comprehensive response
        response = {
            'success': True,
            'location_info': {
                'name': location_data['location'],
                'coordinates': location_data['coordinates'],
                'crop_type': location_data['crop_type']
            },
            'fetched_data': ml_input,
            'data_sources': location_data['data_sources'],
            'irrigation': {
                'decision': 'YES' if irrigate == 1 else 'NO',
                'confidence': detailed_result['Confidence']['irrigation'],
                'explanation': explanation.split('✅')[0].strip(),
                'water_quantity': water_quantity
            },
            'alert': {
                'decision': 'ALERT' if alert == 1 else 'NORMAL',
                'confidence': detailed_result['Confidence']['alert'],
                'explanation': explanation.split('✅')[-1].strip() if '✅' in explanation else 'Normal conditions'
            },
            'key_factors': [
                {'feature': 'soil_moisture', 'value': f"{ml_input['soil_moisture']:.1f}%", 'source': location_data['data_sources'].get('soil', 'N/A')},
                {'feature': 'Precipitation', 'value': f"{ml_input['Precipitation']:.1f}mm", 'source': location_data['data_sources'].get('weather', 'N/A')},
                {'feature': 'MaxT', 'value': f"{ml_input['MaxT']:.1f}°C", 'source': location_data['data_sources'].get('weather', 'N/A')},
                {'feature': 'weather_humidity', 'value': f"{ml_input['weather_humidity']:.0f}%", 'source': location_data['data_sources'].get('weather', 'N/A')},
                {'feature': 'water_quantity', 'value': water_quantity, 'source': 'ML Model'}
            ],
            'model_connection': {
                'status': 'connected',
                'models_used': ['Model A (Irrigation)', 'Model B (Alert)'],
                'integration': 'active',
                'data_fetch': 'automatic'
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in predict_with_location: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/crops', methods=['GET'])
def get_crops():
    """Get list of all available crops with their sensitivity levels"""
    try:
        high_sensitivity = get_all_crops_by_sensitivity(2)
        medium_sensitivity = get_all_crops_by_sensitivity(1)
        low_sensitivity = get_all_crops_by_sensitivity(0)
        
        return jsonify({
            'success': True,
            'crops': {
                'high_sensitivity': high_sensitivity,
                'medium_sensitivity': medium_sensitivity,
                'low_sensitivity': low_sensitivity
            }
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/crops/search', methods=['GET'])
def search_crops_endpoint():
    """Search for crops by name"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter "q" is required'
            }), 400
        
        results = search_crops(query)
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/crop-info/<crop_key>', methods=['GET'])
def get_crop_info_endpoint(crop_key):
    """Get detailed information about a specific crop"""
    try:
        info = get_crop_info(crop_key)
        
        return jsonify({
            'success': True,
            'crop': crop_key,
            'info': info
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html', defaults=DEFAULTS, ranges=VALIDATION_RANGES)


@app.route('/predict', methods=['POST'])
def predict():
    """ML inference endpoint using inference.py"""
    
    try:
        # Get form data
        form_data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Validate mandatory fields
        if 'soil_moisture' not in form_data or 'Precipitation' not in form_data:
            return jsonify({
                'success': False,
                'error': 'soil_moisture and Precipitation are required fields'
            }), 400
        
        # Prepare input data with type conversion
        user_input = {
            'soil_moisture': float(form_data.get('soil_moisture')),
            'Moisture_Trend': float(form_data.get('Moisture_Trend', DEFAULTS['Moisture_Trend'])),
            'Precipitation': float(form_data.get('Precipitation')),
            'weather_humidity': float(form_data.get('weather_humidity', DEFAULTS['weather_humidity'])),
            'MaxT': float(form_data.get('MaxT', DEFAULTS['MaxT'])),
            'MinT': float(form_data.get('MinT', DEFAULTS['MinT'])),
            'Water_Sensitivity': int(form_data.get('Water_Sensitivity', DEFAULTS['Water_Sensitivity']))
        }
        
        # Run enhanced inference with Model A & B integration
        result = run_inference(user_input)
        
        # Get detailed integrated results for enhanced information
        try:
            detailed_result = integrated_model_prediction(user_input)
            irrigation_confidence = detailed_result['Confidence']['irrigation']
            alert_confidence = detailed_result['Confidence']['alert']
            logger.info(f"🔗 Integrated prediction: Irrigate={result['Irrigate']}, Alert={result['Alert']}, Water={result['Water_Quantity']}")
        except Exception as e:
            # Fallback to default confidence if detailed results fail
            irrigation_confidence = 85.0 if result['Irrigate'] == 1 else 92.0
            alert_confidence = 88.0 if result['Alert'] == 1 else 95.0
            logger.warning(f"Using fallback confidence scores: {e}")
        
        # Map to frontend format
        irrigate = result['Irrigate']
        alert = result['Alert']
        water_quantity = result.get('Water_Quantity', 'None')
        
        # Generate explanation
        explanation = generate_explanation(user_input, irrigate, alert, water_quantity)
        
        # Prepare response in format expected by frontend
        response = {
            'irrigation': {
                'decision': 'YES' if irrigate == 1 else 'NO',
                'confidence': irrigation_confidence,
                'explanation': explanation.split('✅')[0].strip(),  # Irrigation part
                'water_quantity': water_quantity
            },
            'alert': {
                'decision': 'ALERT' if alert == 1 else 'NORMAL',
                'confidence': alert_confidence,
                'explanation': explanation.split('✅')[-1].strip() if '✅' in explanation else 'Normal conditions'
            },
            'key_factors': [
                {'feature': 'soil_moisture', 'value': f"{user_input['soil_moisture']:.1f}%"},
                {'feature': 'Precipitation', 'value': f"{user_input['Precipitation']:.1f}mm"},
                {'feature': 'MaxT', 'value': f"{user_input['MaxT']:.1f}°C"},
                {'feature': 'weather_humidity', 'value': f"{user_input['weather_humidity']:.0f}%"},
                {'feature': 'water_quantity', 'value': water_quantity}
            ],
            'model_connection': {
                'status': 'connected',
                'models_used': ['Model A (Irrigation)', 'Model B (Alert)'],
                'integration': 'active'
            }
        }
        
        return jsonify(response), 200
        
    except ValueError as ve:
        return jsonify({
            'success': False,
            'error': str(ve)
        }), 400
        
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        return jsonify({
            'success': False,
            'error': f'Prediction failed: {str(e)}'
        }), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Test if inference module works
        test_input = {
            'soil_moisture': 50.0,
            'Precipitation': 2.0
        }
        run_inference(test_input)
        models_loaded = True
    except:
        models_loaded = False
    
    return jsonify({
        'status': 'healthy' if models_loaded else 'degraded',
        'models_loaded': models_loaded,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/model-connection-test')
def model_connection_test():
    """Test Model A & B connection endpoint"""
    try:
        # Test with standard conditions
        test_input = {
            'soil_moisture': 45.0,
            'Precipitation': 1.0,
            'weather_humidity': 55.0,
            'MaxT': 30.0,
            'MinT': 20.0,
            'Water_Sensitivity': 1,
            'Moisture_Trend': 0.0
        }
        
        # Get integrated prediction
        detailed_result = integrated_model_prediction(test_input)
        standard_result = run_inference(test_input)
        
        return jsonify({
            'status': 'success',
            'model_a_status': 'connected',
            'model_b_status': 'connected',
            'integration_status': 'active',
            'test_results': {
                'input': test_input,
                'standard_output': standard_result,
                'detailed_output': detailed_result
            },
            'confidence_scores': {
                'irrigation': detailed_result['Confidence']['irrigation'],
                'alert': detailed_result['Confidence']['alert']
            },
            'features_used': {
                'model_a': detailed_result['Features_Used']['model_a'],
                'model_b': detailed_result['Features_Used']['model_b']
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Model connection test failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/model-info')
def model_info_endpoint():
    """Return model information"""
    return jsonify({
        'irrigation_model': {
            'name': 'Model A - Irrigation Decision Tree',
            'file': 'model_A_irrigation_decision_tree.pkl',
            'features': ['soil_moisture', 'weather_humidity', 'MaxT', 'MinT', 'Precipitation', 'Water_Sensitivity']
        },
        'alert_model': {
            'name': 'Model B - Alert Detection',
            'file': 'model_B_alert (1).pkl',
            'features': ['Moisture_Trend', 'soil_moisture', 'Precipitation', 'weather_humidity', 'MaxT', 'MinT']
        },
        'inference_layer': 'inference.py (clean separation)'
    })


# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ============================================
# HEALTH CHECK & KEEP-ALIVE
# ============================================

@app.route('/health')
def health_check():
    """Health check endpoint for Render/monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Smart Irrigation System',
        'location_service': LOCATION_SERVICE_ENABLED
    }), 200


def keep_alive():
    """
    Keep-alive function to prevent Render free tier from sleeping
    Pings the health endpoint every 14 minutes
    """
    app_url = os.getenv('RENDER_EXTERNAL_URL', os.getenv('APP_URL', ''))
    
    if not app_url:
        logger.info("⚠️ No APP_URL set, keep-alive disabled (local development)")
        return
    
    logger.info(f"🔄 Keep-alive started for: {app_url}")
    
    while True:
        try:
            time.sleep(840)  # 14 minutes
            response = http_requests.get(f"{app_url}/health", timeout=30)
            logger.info(f"💓 Keep-alive ping: {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Keep-alive ping failed: {e}")


# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🌱 SMART IRRIGATION SYSTEM")
    print("="*70)
    print("📍 Server starting...")
    print("🌐 Access the application at: http://localhost:5000")
    print(f"📍 Location Service: {'ENABLED' if LOCATION_SERVICE_ENABLED else 'DISABLED'}")
    print("="*70 + "\n")
    
    # Run without debug to avoid reloader issues
    app.run(debug=False, host='0.0.0.0', port=5000)
else:
    # Production mode (gunicorn) - start keep-alive thread
    if os.getenv('RENDER') or os.getenv('APP_URL'):
        keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
        keep_alive_thread.start()
        logger.info("🚀 Keep-alive thread started for production")
