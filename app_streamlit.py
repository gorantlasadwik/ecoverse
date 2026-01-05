"""
Smart Irrigation System - Streamlit Interface
============================================
Alternative interface for the irrigation prediction system
Connects to the same .pkl model files as the Flask app
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the inference module to connect to .pkl files
from inference import run_inference, integrated_model_prediction, DEFAULTS

# Configure page
st.set_page_config(
    page_title="Smart Irrigation System",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Header
st.title("🌱 Smart Irrigation Decision System")
st.markdown("**AI-powered irrigation recommendations using trained ML models**")

# Sidebar for inputs
st.sidebar.header("🌾 Field Parameters")

# Input parameters with defaults
soil_moisture = st.sidebar.slider(
    "Soil Moisture (%)", 
    min_value=30.0, max_value=70.0, 
    value=50.0, step=0.1,
    help="Current soil moisture percentage"
)

moisture_trend = st.sidebar.slider(
    "Moisture Trend", 
    min_value=-5.0, max_value=5.0, 
    value=0.0, step=0.1,
    help="Rate of change in soil moisture"
)

precipitation = st.sidebar.slider(
    "Precipitation (mm)", 
    min_value=0.0, max_value=15.0, 
    value=0.0, step=0.1,
    help="Expected or recent rainfall"
)

weather_humidity = st.sidebar.slider(
    "Humidity (%)", 
    min_value=20, max_value=100, 
    value=50, step=1,
    help="Atmospheric humidity percentage"
)

max_temp = st.sidebar.slider(
    "Maximum Temperature (°C)", 
    min_value=15.0, max_value=50.0, 
    value=30.0, step=0.5,
    help="Daily maximum temperature"
)

min_temp = st.sidebar.slider(
    "Minimum Temperature (°C)", 
    min_value=5.0, max_value=40.0, 
    value=22.0, step=0.5,
    help="Daily minimum temperature"
)

water_sensitivity = st.sidebar.selectbox(
    "Crop Water Sensitivity",
    options=[0, 1, 2],
    index=1,
    format_func=lambda x: {0: "Low", 1: "Medium", 2: "High"}[x],
    help="Crop's sensitivity to water stress"
)

# Scenario presets
st.sidebar.markdown("### 🎯 Quick Scenarios")
if st.sidebar.button("🔥 Dry Field"):
    soil_moisture = 42.0
    moisture_trend = -3.5
    precipitation = 0.0
    weather_humidity = 25
    max_temp = 38.0
    min_temp = 28.0
    water_sensitivity = 2

if st.sidebar.button("🌧️ Rain Expected"):
    soil_moisture = 58.0
    moisture_trend = 2.5
    precipitation = 8.5
    weather_humidity = 85
    max_temp = 24.0
    min_temp = 18.0
    water_sensitivity = 0

if st.sidebar.button("✅ Healthy Field"):
    soil_moisture = 52.0
    moisture_trend = 0.5
    precipitation = 2.0
    weather_humidity = 60
    max_temp = 28.0
    min_temp = 20.0
    water_sensitivity = 1

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📊 Current Parameters")
    
    # Display input parameters
    params_df = pd.DataFrame({
        'Parameter': [
            'Soil Moisture', 'Moisture Trend', 'Precipitation', 
            'Humidity', 'Max Temperature', 'Min Temperature', 
            'Water Sensitivity'
        ],
        'Value': [
            f"{soil_moisture:.1f}%", f"{moisture_trend:.1f}", f"{precipitation:.1f} mm",
            f"{weather_humidity}%", f"{max_temp:.1f}°C", f"{min_temp:.1f}°C",
            {0: "Low", 1: "Medium", 2: "High"}[water_sensitivity]
        ]
    })
    
    st.dataframe(params_df, use_container_width=True)

with col2:
    st.header("🎮 Actions")
    
    if st.button("🔮 Run Prediction", type="primary", use_container_width=True):
        # Prepare input for inference
        user_input = {
            'soil_moisture': soil_moisture,
            'Moisture_Trend': moisture_trend,
            'Precipitation': precipitation,
            'weather_humidity': weather_humidity,
            'MaxT': max_temp,
            'MinT': min_temp,
            'Water_Sensitivity': water_sensitivity
        }
        
        try:
            # Get prediction results using the same .pkl files as Flask app
            result = run_inference(user_input)
            detailed_result = integrated_model_prediction(user_input)
            
            # Display results
            st.header("🎯 Prediction Results")
            
            # Irrigation decision
            irrigate = result['Irrigate']
            irrigation_decision = "YES" if irrigate == 1 else "NO"
            irrigation_color = "🟢" if irrigate == 1 else "🔴"
            
            # Alert status
            alert = result['Alert']
            alert_status = "ALERT" if alert == 1 else "NORMAL"
            alert_color = "🟠" if alert == 1 else "🟢"
            
            # Water quantity
            water_quantity = result.get('Water_Quantity', 'None')
            water_color = {"Low": "🔵", "Medium": "🟡", "High": "🔴", "None": "⚪"}[water_quantity]
            
            # Results display
            st.markdown("### 💧 Irrigation Decision")
            st.markdown(f"## {irrigation_color} **{irrigation_decision}**")
            
            st.markdown("### 🛡️ Alert Status")
            st.markdown(f"## {alert_color} **{alert_status}**")
            
            st.markdown("### 💦 Water Quantity")
            st.markdown(f"## {water_color} **{water_quantity}**")
            
            # Confidence scores
            if 'Confidence' in detailed_result:
                st.markdown("### 📈 Confidence Levels")
                irrigation_conf = detailed_result['Confidence']['irrigation']
                alert_conf = detailed_result['Confidence']['alert']
                
                col_conf1, col_conf2 = st.columns(2)
                with col_conf1:
                    st.metric("Irrigation Confidence", f"{irrigation_conf:.1f}%")
                with col_conf2:
                    st.metric("Alert Confidence", f"{alert_conf:.1f}%")
            
            # Model information
            st.markdown("### 🤖 Model Information")
            st.info("**Connected to trained ML models:**\\n- Model A: Irrigation Decision Tree\\n- Model B: Alert Detection Tree\\n- Both models loaded from .pkl files successfully!")
            
        except Exception as e:
            st.error(f"❌ Error running prediction: {str(e)}")
            st.error("Please ensure the .pkl model files are available in the models/ directory")

# Footer
st.markdown("---")
st.markdown("**🌱 Smart Irrigation System** | Powered by trained ML models (.pkl files)")
st.markdown("*This Streamlit interface connects to the same models used by the Flask application*")
