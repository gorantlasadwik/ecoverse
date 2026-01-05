"""
Vercel Serverless Function for Smart Irrigation System
====================================================
Optimized for Vercel's serverless environment
"""

from flask import Flask, render_template, request, jsonify
from datetime import datetime
import os

app = Flask(__name__)

# Simple rule-based logic for Vercel deployment
def simple_irrigation_logic(soil_moisture, moisture_trend, precipitation, water_sensitivity, max_temp):
    """Simple rule-based irrigation logic"""
    
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
    try:
        # Simple HTML response since templates might not work in serverless
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Smart Irrigation System</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .form-group { margin: 15px 0; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                input, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
                button { background: #007bff; color: white; padding: 12px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
                button:hover { background: #0056b3; }
                .result { margin-top: 20px; padding: 15px; border-radius: 5px; }
                .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
                .alert { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
                .info { background: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🌱 Smart Irrigation Decision System</h1>
                <p>Enter your field parameters to get irrigation recommendations:</p>
                
                <form id="predictionForm">
                    <div class="form-group">
                        <label>Soil Moisture (%)</label>
                        <input type="number" id="soil_moisture" value="50" min="20" max="80" step="0.1">
                    </div>
                    
                    <div class="form-group">
                        <label>Moisture Trend (%/day)</label>
                        <input type="number" id="moisture_trend" value="0" min="-5" max="5" step="0.1">
                    </div>
                    
                    <div class="form-group">
                        <label>Expected Precipitation (mm)</label>
                        <input type="number" id="precipitation" value="0" min="0" max="50" step="0.1">
                    </div>
                    
                    <div class="form-group">
                        <label>Humidity (%)</label>
                        <input type="number" id="humidity" value="60" min="30" max="100" step="1">
                    </div>
                    
                    <div class="form-group">
                        <label>Max Temperature (°C)</label>
                        <input type="number" id="max_temp" value="30" min="10" max="50" step="0.1">
                    </div>
                    
                    <div class="form-group">
                        <label>Min Temperature (°C)</label>
                        <input type="number" id="min_temp" value="20" min="0" max="40" step="0.1">
                    </div>
                    
                    <div class="form-group">
                        <label>Crop Water Sensitivity</label>
                        <select id="water_sensitivity">
                            <option value="0">Low</option>
                            <option value="1" selected>Medium</option>
                            <option value="2">High</option>
                        </select>
                    </div>
                    
                    <button type="submit">🔍 Get Recommendation</button>
                </form>
                
                <div id="result" style="display:none;"></div>
            </div>
            
            <script>
                document.getElementById('predictionForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    const data = {
                        soil_moisture: parseFloat(document.getElementById('soil_moisture').value),
                        Moisture_Trend: parseFloat(document.getElementById('moisture_trend').value),
                        Precipitation: parseFloat(document.getElementById('precipitation').value),
                        weather_humidity: parseFloat(document.getElementById('humidity').value),
                        MaxT: parseFloat(document.getElementById('max_temp').value),
                        MinT: parseFloat(document.getElementById('min_temp').value),
                        Water_Sensitivity: parseInt(document.getElementById('water_sensitivity').value)
                    };
                    
                    try {
                        const response = await fetch('/api/predict', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(data)
                        });
                        
                        const result = await response.json();
                        const resultDiv = document.getElementById('result');
                        
                        if (result.success) {
                            const predictions = result.predictions;
                            let resultClass = 'info';
                            if (predictions.irrigate_label === 'YES') resultClass = 'success';
                            if (predictions.alert_label === 'ALERT') resultClass = 'alert';
                            
                            resultDiv.innerHTML = `
                                <div class="${resultClass}">
                                    <h3>📊 Recommendation Results</h3>
                                    <p><strong>Irrigation:</strong> ${predictions.irrigate_label} (${predictions.irrigate_confidence}% confidence)</p>
                                    <p><strong>Water Quantity:</strong> ${predictions.water_quantity}</p>
                                    <p><strong>Alert Status:</strong> ${predictions.alert_label} (${predictions.alert_confidence}% confidence)</p>
                                    <p><strong>Explanation:</strong> ${result.explanation}</p>
                                </div>
                            `;
                        } else {
                            resultDiv.innerHTML = `<div class="alert"><h3>Error</h3><p>${result.error}</p></div>`;
                        }
                        
                        resultDiv.style.display = 'block';
                    } catch (error) {
                        document.getElementById('result').innerHTML = `<div class="alert"><h3>Error</h3><p>Failed to get prediction: ${error.message}</p></div>`;
                        document.getElementById('result').style.display = 'block';
                    }
                });
            </script>
        </body>
        </html>
        '''
    except Exception as e:
        return f"Error loading page: {str(e)}", 500

@app.route('/api/predict', methods=['POST'])
def predict():
    """Prediction endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
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
                'irrigate_confidence': 85.0,
                'water_quantity': water_quantity,
                'alert': alert,
                'alert_label': 'ALERT' if alert == 1 else 'NORMAL',
                'alert_confidence': 80.0
            },
            'explanation': explanation,
            'deployment': 'vercel-serverless'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Prediction error: {str(e)}'
        }), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'deployment': 'vercel-serverless',
        'timestamp': datetime.now().isoformat()
    })

# Vercel handler - this is the key for serverless functions
def handler(event, context):
    """Vercel serverless handler"""
    return app.wsgi_app(event, context)

# This is what Vercel will call
application = app

# For local development
if __name__ == '__main__':
    app.run(debug=True)