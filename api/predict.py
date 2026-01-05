"""
Simple Vercel Serverless Function for Smart Irrigation
====================================================
"""

from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        try:
            path = urlparse(self.path).path
            
            if path == '/' or path == '':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                html = '''
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
                        input, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
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
                                moisture_trend: parseFloat(document.getElementById('moisture_trend').value),
                                precipitation: parseFloat(document.getElementById('precipitation').value),
                                humidity: parseFloat(document.getElementById('humidity').value),
                                max_temp: parseFloat(document.getElementById('max_temp').value),
                                min_temp: parseFloat(document.getElementById('min_temp').value),
                                water_sensitivity: parseInt(document.getElementById('water_sensitivity').value)
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
                
                self.wfile.write(html.encode())
                
            elif path == '/health':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    'status': 'healthy',
                    'deployment': 'vercel-serverless',
                    'timestamp': datetime.now().isoformat()
                }
                
                self.wfile.write(json.dumps(response).encode())
            
            else:
                self.send_response(404)
                self.end_headers()
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def do_POST(self):
        """Handle POST requests"""
        try:
            path = urlparse(self.path).path
            
            if path == '/predict':
                # Read POST data
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                # Simple irrigation logic
                irrigate, alert, water_quantity = self.simple_irrigation_logic(
                    data.get('soil_moisture', 50.0),
                    data.get('moisture_trend', 0.0),
                    data.get('precipitation', 0.0),
                    data.get('water_sensitivity', 1),
                    data.get('max_temp', 30.0)
                )
                
                # Generate explanation
                explanation = self.generate_explanation(irrigate, alert, water_quantity, data)
                
                response = {
                    'success': True,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'inputs': data,
                    'predictions': {
                        'irrigate': irrigate,
                        'irrigate_label': 'YES' if irrigate == 1 else 'NO',
                        'irrigate_confidence': 85.0,
                        'water_quantity': water_quantity,
                        'alert': alert,
                        'alert_label': 'ALERT' if alert == 1 else 'NORMAL',
                        'alert_confidence': 80.0
                    },
                    'explanation': explanation
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            else:
                self.send_response(404)
                self.end_headers()
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {'success': False, 'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode())

    def simple_irrigation_logic(self, soil_moisture, moisture_trend, precipitation, water_sensitivity, max_temp):
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

    def generate_explanation(self, irrigate, alert, water_quantity, data):
        """Generate explanation for the decision"""
        explanation_parts = []
        
        if irrigate == 1:
            explanation_parts.append(f"💧 Irrigation recommended: soil moisture {data.get('soil_moisture', 0)}%")
            if data.get('precipitation', 0) < 1.0:
                explanation_parts.append("minimal rainfall expected")
            if data.get('water_sensitivity', 1) == 2:
                explanation_parts.append("high crop water sensitivity")
            explanation_parts.append(f"Water quantity: {water_quantity}")
        else:
            explanation_parts.append("❌ No irrigation needed: adequate moisture levels")
        
        if alert == 1:
            if data.get('moisture_trend', 0) < -2.0:
                explanation_parts.append(f"🚨 Alert: rapid drying (trend: {data.get('moisture_trend', 0)})")
            elif data.get('soil_moisture', 0) < 30:
                explanation_parts.append("🚨 Alert: critically low moisture")
            else:
                explanation_parts.append("🚨 Alert: stress conditions detected")
        
        return ". ".join(explanation_parts) + "."