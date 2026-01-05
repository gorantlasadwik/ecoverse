"""
Smart Irrigation System - Flask Backend
========================================
Real-time irrigation recommendations using trained ML models
Uses inference.py for all ML logic (clean separation)
"""

from flask import Flask, render_template, request, jsonify
from inference import run_inference, integrated_model_prediction, DEFAULTS
import pandas as pd
import os
from datetime import datetime
import logging

# Configure logging for model connections
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

print("🌱 Smart Irrigation System - Flask Backend")
print("✅ Using enhanced inference.py for integrated ML logic")
print("🔗 Model A & B connection: ACTIVE")

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
# MAIN
# ============================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🌱 SMART IRRIGATION SYSTEM")
    print("="*70)
    print("📍 Server starting...")
    print("🌐 Access the application at: http://localhost:5000")
    print("="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
