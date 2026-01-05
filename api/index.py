"""
Vercel-Optimized Smart Irrigation System
=======================================
Lightweight version optimized for serverless deployment
"""

from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Simple rule-based logic for Vercel deployment (fallback)
def simple_irrigation_logic(soil_moisture, moisture_trend, precipitation, water_sensitivity, max_temp):
    """Simple rule-based irrigation logic as fallback for Vercel deployment"""
    
    # Irrigation decision
    irrigate = 0
    if soil_moisture < 45 and precipitation < 1.0:
        irrigate = 1
    elif water_sensitivity == 2 and soil_moisture < 50:  # High sensitivity crops
        irrigate = 1
    
    # Alert decision
    alert = 0
    if moisture_trend < -2.0:  # Rapid drying
        alert = 1
    elif soil_moisture < 30:  # Critically low
        alert = 1
    elif soil_moisture < 40 and precipitation < 0.5 and max_temp > 38:
        alert = 1
    
    # Water quantity estimation
    water_quantity = "LOW"
    if irrigate == 1:
        if soil_moisture < 35 or (moisture_trend < -2.5 and water_sensitivity == 2):
            water_quantity = "HIGH"
        elif soil_moisture < 50 and (moisture_trend < -1.0 or water_sensitivity >= 1):
            water_quantity = "MEDIUM"
        else:
            water_quantity = "LOW"
    
    return irrigate, alert, water_quantity

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Prediction endpoint using simplified logic for Vercel"""
    try:
        data = request.get_json()
        
        # Extract inputs with defaults
        soil_moisture = float(data.get('soil_moisture', 50.0))
        moisture_trend = float(data.get('Moisture_Trend', 0.0))
        precipitation = float(data.get('Precipitation', 0.0))
        weather_humidity = float(data.get('weather_humidity', 60.0))
        max_temp = float(data.get('MaxT', 30.0))
        min_temp = float(data.get('MinT', 20.0))
        water_sensitivity = int(data.get('Water_Sensitivity', 1))
        
        # Run simplified prediction
        irrigate, alert, water_quantity = simple_irrigation_logic(
            soil_moisture, moisture_trend, precipitation, water_sensitivity, max_temp
        )
        
        # Generate explanation
        explanation_parts = []
        if irrigate == 1:
            explanation_parts.append(f"💧 Irrigation recommended: soil moisture {soil_moisture}%")
            if precipitation < 1.0:
                explanation_parts.append("minimal rainfall expected")
            if water_sensitivity == 2:
                explanation_parts.append("high crop water sensitivity")
            explanation_parts.append(f"Water quantity: {water_quantity}")
        else:
            explanation_parts.append("❌ No irrigation needed: adequate moisture levels")
        
        if alert == 1:
            if moisture_trend < -2.0:
                explanation_parts.append(f"🚨 Alert: rapid drying (trend: {moisture_trend})")
            elif soil_moisture < 30:
                explanation_parts.append("🚨 Alert: critically low moisture")
            else:
                explanation_parts.append("🚨 Alert: stress conditions detected")
        
        explanation = ". ".join(explanation_parts) + "."
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'inputs': {
                'soil_moisture': soil_moisture,
                'Moisture_Trend': moisture_trend,
                'Precipitation': precipitation,
                'weather_humidity': weather_humidity,
                'MaxT': max_temp,
                'MinT': min_temp,
                'Water_Sensitivity': water_sensitivity
            },
            'predictions': {
                'irrigate': irrigate,
                'irrigate_label': 'YES' if irrigate == 1 else 'NO',
                'irrigate_confidence': 85.0,  # Simulated confidence
                'water_quantity': water_quantity,
                'alert': alert,
                'alert_label': 'ALERT' if alert == 1 else 'NORMAL',
                'alert_confidence': 80.0  # Simulated confidence
            },
            'explanation': explanation,
            'deployment': 'vercel-optimized'
        })
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'deployment': 'vercel-serverless',
        'timestamp': datetime.now().isoformat()
    })

# Vercel handler
def handler(request, context):
    return app

# Export for Vercel
application = app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)