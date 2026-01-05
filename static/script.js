// ============================================
// SMART IRRIGATION DECISION SYSTEM - FRONTEND
// ============================================

const el = (id) => document.getElementById(id);

// Scenario presets
const SCENARIOS = {
  dry: {
    soil_moisture: 42,
    Moisture_Trend: -3.5,
    Precipitation: 0,
    weather_humidity: 25,
    MaxT: 38,
    MinT: 28,
    Water_Sensitivity: 2,
    name: 'Dry Field'
  },
  rain: {
    soil_moisture: 58,
    Moisture_Trend: 2.5,
    Precipitation: 8.5,
    weather_humidity: 85,
    MaxT: 24,
    MinT: 18,
    Water_Sensitivity: 0,
    name: 'Rain Expected'
  },
  leak: {
    soil_moisture: 64,
    Moisture_Trend: 4.8,
    Precipitation: 0.5,
    weather_humidity: 45,
    MaxT: 32,
    MinT: 24,
    Water_Sensitivity: 1,
    name: 'Anomaly/Leak Detected'
  },
  healthy: {
    soil_moisture: 52,
    Moisture_Trend: 0.5,
    Precipitation: 2.0,
    weather_humidity: 60,
    MaxT: 28,
    MinT: 20,
    Water_Sensitivity: 1,
    name: 'Healthy Field'
  }
};

// Input configuration
const inputs = [
  { id: 'soil_moisture', out: 'soil_moisture_value', fmt: (v) => Number(v).toFixed(1) },
  { id: 'Moisture_Trend', out: 'Moisture_Trend_value', fmt: (v) => Number(v).toFixed(1) },
  { id: 'soil_temp', out: 'soil_temp_value', fmt: (v) => `${Number(v).toFixed(1)}°C` },
  { id: 'Precipitation', out: 'Precipitation_value', fmt: (v) => `${Number(v).toFixed(1)} mm` },
  { id: 'weather_humidity', out: 'weather_humidity_value', fmt: (v) => `${parseInt(v,10)}%` },
  { id: 'MaxT', out: 'MaxT_value', fmt: (v) => `${Number(v).toFixed(1)}°C` },
  { id: 'MinT', out: 'MinT_value', fmt: (v) => `${Number(v).toFixed(1)}°C` },
];

// ============================================
// LOAD SCENARIO PRESET
// ============================================
function loadScenario(type) {
  const scenario = SCENARIOS[type];
  if (!scenario) return;
  
  // Set all values
  el('soil_moisture').value = scenario.soil_moisture;
  el('Moisture_Trend').value = scenario.Moisture_Trend;
  el('Precipitation').value = scenario.Precipitation;
  el('weather_humidity').value = scenario.weather_humidity;
  el('MaxT').value = scenario.MaxT;
  el('MinT').value = scenario.MinT;
  el('Water_Sensitivity').value = scenario.Water_Sensitivity;
  
  // Set optional fields to defaults if not in scenario
  if (el('soil_temp')) el('soil_temp').value = 18;
  if (el('field_status')) el('field_status').value = 'normal';
  
  // Update displays
  inputs.forEach(inp => {
    const value = el(inp.id).value;
    el(inp.out).textContent = inp.fmt(value);
  });
  
  renderPayload();
  updateTrends(scenario);
  updateSystemStatus(`Loaded: ${scenario.name}`);
}

// ============================================
// UPDATE DASHBOARD STATS
// ============================================
function updateSystemStatus(status = 'Ready') {
  el('systemStatus').textContent = status;
  el('lastUpdated').textContent = new Date().toLocaleTimeString();
}

function updateTrends(data) {
  // Update soil moisture trend
  const moistureTrend = data.Moisture_Trend || 0;
  const trendMoisture = el('trendMoisture');
  if (moistureTrend < -1) {
    trendMoisture.innerHTML = '<img src="https://api.iconify.design/lucide-arrow-down.svg?color=%23dc2626" alt="Down" class="trend-arrow"/>Decreasing';
  } else if (moistureTrend > 1) {
    trendMoisture.innerHTML = '<img src="https://api.iconify.design/lucide-arrow-up.svg?color=%2316a34a" alt="Up" class="trend-arrow"/>Increasing';
  } else {
    trendMoisture.innerHTML = '<img src="https://api.iconify.design/lucide-minus.svg?color=%236b7280" alt="Stable" class="trend-arrow"/>Stable';
  }
  
  // Update temperature trend
  const maxT = data.MaxT || 25;
  const trendTemp = el('trendTemperature');
  if (maxT > 35) {
    trendTemp.innerHTML = '<img src="https://api.iconify.design/lucide-arrow-up.svg?color=%23ea580c" alt="Up" class="trend-arrow"/>Increasing (Hot)';
  } else if (maxT < 20) {
    trendTemp.innerHTML = '<img src="https://api.iconify.design/lucide-arrow-down.svg?color=%230ea5e9" alt="Down" class="trend-arrow"/>Decreasing (Cool)';
  } else {
    trendTemp.innerHTML = '<img src="https://api.iconify.design/lucide-minus.svg?color=%236b7280" alt="Stable" class="trend-arrow"/>Moderate';
  }
  
  // Update rain probability
  const precip = data.Precipitation || 0;
  const trendRain = el('trendRain');
  if (precip > 5) {
    trendRain.innerHTML = '<span class="probability-badge probability-high">High (85%)</span>';
  } else if (precip > 2) {
    trendRain.innerHTML = '<span class="probability-badge probability-medium">Medium (45%)</span>';
  } else {
    trendRain.innerHTML = '<span class="probability-badge probability-low">Low (15%)</span>';
  }
}

// ============================================
// PAYLOAD BUILDER
// ============================================
function payload() {
  return {
    soil_moisture: Number(el('soil_moisture').value),
    Moisture_Trend: Number(el('Moisture_Trend').value),
    Precipitation: Number(el('Precipitation').value),
    weather_humidity: parseInt(el('weather_humidity').value, 10),
    MaxT: Number(el('MaxT').value),
    MinT: Number(el('MinT').value),
    Water_Sensitivity: parseInt(el('Water_Sensitivity').value, 10),
    soil_temp: Number(el('soil_temp')?.value || 18),
    field_status: el('field_status')?.value || 'normal'
  };
}

// ============================================
// RENDER PAYLOAD PREVIEW
// ============================================
function renderPayload() {
  const p = payload();
  el('payloadPreview').textContent = JSON.stringify(p, null, 2);
}

// ============================================
// SET BADGE STYLES
// ============================================
function setBadge(badgeId, text, colorHex, iconName) {
  const badge = el(badgeId);
  
  // Handle different badge types
  let icon, txt;
  if (badgeId === 'decisionBadge') {
    icon = el('decisionIcon');
    txt = el('decisionText');
  } else if (badgeId === 'alertBadge') {
    icon = el('alertIcon');
    txt = el('alertText');
  } else if (badgeId === 'waterQuantityBadge') {
    icon = el('waterQuantityIcon');
    txt = el('waterQuantityText');
  } else {
    // Fallback for other badge types
    icon = el(badgeId.replace('Badge', 'Icon'));
    txt = el(badgeId.replace('Badge', 'Text'));
  }
  
  if (txt) txt.textContent = text;
  if (badge) {
    badge.style.backgroundColor = colorHex.bg;
    badge.style.color = colorHex.fg;
  }
  if (icon) {
    icon.src = `https://api.iconify.design/lucide-${iconName}.svg?color=${encodeURIComponent(colorHex.fg)}`;
  }
}

// ============================================
// VALIDATION
// ============================================
function validateMandatory() {
  const errors = [];
  const sm = Number(el('soil_moisture').value);
  const pr = Number(el('Precipitation').value);
  
  if (isNaN(sm) || sm < 40 || sm > 65) {
    errors.push('Soil Moisture must be between 40 and 65.');
  }
  if (isNaN(pr) || pr < 0 || pr > 10) {
    errors.push('Precipitation must be between 0 and 10.');
  }
  
  return errors;
}

// ============================================
// DOWNLOAD JSON
// ============================================
function downloadJSON(data, filename = 'irrigation_payload.json') {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ============================================
// SHOW/HIDE CONFIDENCE
// ============================================
function showConfidence(type, confidence) {
  const confidenceEl = el(type === 'decision' ? 'decisionConfidence' : 'alertConfidence');
  const valueEl = el(type === 'decision' ? 'decisionConfidenceValue' : 'alertConfidenceValue');
  const barEl = el(type === 'decision' ? 'decisionConfidenceBar' : 'alertConfidenceBar');
  
  if (confidenceEl && valueEl && barEl) {
    confidenceEl.style.display = 'block';
    valueEl.textContent = confidence.toFixed(1) + '%';
    barEl.style.width = confidence + '%';
    
    // Color coding
    barEl.className = 'confidence-bar-fill';
    if (confidence >= 80) {
      barEl.style.backgroundColor = '#10b981';
    } else if (confidence >= 60) {
      barEl.style.backgroundColor = '#f59e0b';
    } else {
      barEl.style.backgroundColor = '#ef4444';
    }
  }
}

function hideConfidence() {
  const decisionConf = el('decisionConfidence');
  const alertConf = el('alertConfidence');
  if (decisionConf) decisionConf.style.display = 'none';
  if (alertConf) alertConf.style.display = 'none';
}

// ============================================
// UPDATE EXPLANATION
// ============================================
function updateExplanation(data) {
  const explanationEl = el('explanationContent');
  if (!explanationEl) return;
  
  let html = '<div class="explanation-sections">';
  
  // Irrigation explanation
  if (data.irrigation && data.irrigation.explanation) {
    html += '<div class="explanation-section">';
    html += '<h4>💧 Irrigation Analysis</h4>';
    html += '<p>' + data.irrigation.explanation + '</p>';
    
    // Add water quantity information if available
    if (data.irrigation.water_quantity && data.irrigation.water_quantity !== 'None') {
      html += '<p><strong>Recommended Water Amount:</strong> ' + data.irrigation.water_quantity + '</p>';
    }
    
    html += '</div>';
  }
  
  // Alert explanation
  if (data.alert && data.alert.explanation) {
    html += '<div class="explanation-section">';
    html += '<h4>🛡️ Alert Analysis</h4>';
    html += '<p>' + data.alert.explanation + '</p>';
    html += '</div>';
  }
  
  // Key factors
  if (data.key_factors && data.key_factors.length > 0) {
    html += '<div class="explanation-section">';
    html += '<h4>🔑 Key Contributing Factors</h4>';
    html += '<ul>';
    data.key_factors.forEach(factor => {
      html += `<li><strong>${factor.feature}:</strong> ${factor.value}</li>`;
    });
    html += '</ul>';
    html += '</div>';
  }
  
  html += '</div>';
  explanationEl.innerHTML = html;
}

// ============================================
// RECOMMENDED ACTION
// ============================================
function showRecommendation(irrigationDecision, alertDecision, data, waterQuantity) {
  const card = el('recommendationCard');
  const text = el('recommendationText');
  const details = el('recommendationDetails');
  
  if (!card || !text || !details) return;
  
  card.style.display = 'block';
  
  let recommendation = '';
  let detailsList = [];
  
  if (irrigationDecision === 'YES') {
    const precip = data.Precipitation || 0;
    const moisture = data.soil_moisture || 50;
    
    if (precip > 5) {
      recommendation = '⏸️ Delay irrigation for 12-24 hours due to expected rainfall';
      detailsList.push('Monitor soil moisture after rain event');
      detailsList.push('Resume irrigation if moisture drops below 48%');
    } else if (moisture < 45) {
      recommendation = '💧 Initiate irrigation immediately - soil moisture critically low';
      if (waterQuantity) {
        detailsList.push(`Apply ${waterQuantity.toLowerCase()} amount of water`);
        if (waterQuantity === 'High') {
          detailsList.push('Run irrigation for 3-4 hours');
        } else if (waterQuantity === 'Medium') {
          detailsList.push('Run irrigation for 2-3 hours');
        } else {
          detailsList.push('Run irrigation for 1-2 hours');
        }
      } else {
        detailsList.push('Run irrigation for 2-3 hours');
      }
      detailsList.push('Recheck moisture levels after 6 hours');
    } else {
      recommendation = '✅ Proceed with scheduled irrigation';
      if (waterQuantity && waterQuantity !== 'None') {
        detailsList.push(`Apply ${waterQuantity.toLowerCase()} amount of water`);
        detailsList.push('Standard irrigation duration recommended');
      } else {
        detailsList.push('Standard irrigation duration recommended');
      }
      detailsList.push('Monitor field response over next 24 hours');
    }
  } else {
    recommendation = '🛑 No irrigation needed at this time';
    detailsList.push('Current soil moisture levels are adequate');
    detailsList.push('Continue monitoring - next check in 12 hours');
  }
  
  if (alertDecision === 'ALERT') {
    recommendation += '\n\n⚠️ ALERT: Inspect irrigation system for potential issues';
    detailsList.push('🔍 Check for: leaks, blockages, sensor malfunction');
    detailsList.push('🔧 Verify all equipment is functioning normally');
  }
  
  text.textContent = recommendation;
  details.innerHTML = '<ul class="recommendation-list">' + 
    detailsList.map(d => `<li>${d}</li>`).join('') + 
    '</ul>';
  
  // Update field health
  if (alertDecision === 'ALERT') {
    el('fieldHealth').textContent = 'Attention Required';
    el('activeAlerts').textContent = '1';
  } else {
    el('fieldHealth').textContent = irrigationDecision === 'YES' ? 'Needs Water' : 'Optimal';
    el('activeAlerts').textContent = '0';
  }
}

// ============================================
// EVENT LISTENERS
// ============================================

// Input field listeners
inputs.forEach(({ id, out, fmt }) => {
  const input = el(id);
  if (input) {
    input.addEventListener('input', () => {
      const output = el(out);
      if (output) {
        output.textContent = fmt(input.value);
      }
      renderPayload();
    });
  }
});

// Water Sensitivity change
const waterSensitivity = el('Water_Sensitivity');
if (waterSensitivity) {
  waterSensitivity.addEventListener('change', renderPayload);
}

// Reset button
el('resetBtn').addEventListener('click', () => {
  // Reset all inputs to defaults
  el('soil_moisture').value = 50;
  el('Moisture_Trend').value = 0;
  el('Precipitation').value = 0;
  el('weather_humidity').value = 50;
  el('MaxT').value = 30;
  el('MinT').value = 22;
  el('Water_Sensitivity').value = 1;
  
  // Update displays
  inputs.forEach(({ id, out, fmt }) => {
    const output = el(out);
    const input = el(id);
    if (output && input) {
      output.textContent = fmt(input.value);
    }
  });
  
  renderPayload();
  
  // Reset badges
  setBadge('decisionBadge', 'Pending', { bg: '#f8fafc', fg: '#0f172a' }, 'help-circle');
  setBadge('alertBadge', 'NORMAL', { bg: '#f0f9ff', fg: '#075985' }, 'shield-check');
  hideConfidence();
  
  // Reset explanation
  const explanationEl = el('explanationContent');
  if (explanationEl) {
    explanationEl.innerHTML = '<p>The ML model combines soil, weather, and temporal signals to output two core decisions: <strong>Irrigation Decision (YES/NO)</strong> and <strong>Alert Status (NORMAL/ALERT)</strong>. Feature importance guides transparency and aligns with agronomic best practices.</p><p>Run inference to see detailed decision reasoning and feature importance analysis.</p>';
  }
});

// Download button
el('downloadBtn').addEventListener('click', () => {
  downloadJSON(payload());
});

// Run inference button
el('runBtn').addEventListener('click', async () => {
  // Validate mandatory fields
  const errs = validateMandatory();
  if (errs.length) {
    setBadge('decisionBadge', 'Validation Error', { bg: '#fef2f2', fg: '#b91c1c' }, 'x-circle');
    setBadge('alertBadge', 'ALERT', { bg: '#fff7ed', fg: '#c2410c' }, 'alert-triangle');
    alert(errs.join('\n'));
    return;
  }

  const reqPayload = payload();
  const btn = el('runBtn');
  const originalText = btn.innerHTML;
  
  // Show loading state
  btn.disabled = true;
  btn.innerHTML = '<span>Processing...</span>';

  try {
    // Call Flask backend /predict endpoint
    const res = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reqPayload)
    });

    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }

    const data = await res.json();

    // Update Irrigation Decision
    if (data.irrigation) {
      const decision = data.irrigation.decision;
      const confidence = data.irrigation.confidence;
      
      const decisionColor = decision === 'YES'
        ? { bg: '#ecfdf5', fg: '#065f46' }
        : { bg: '#f1f5f9', fg: '#0f172a' };
      const decisionIcon = decision === 'YES' ? 'check-circle' : 'circle-slash';
      
      setBadge('decisionBadge', decision, decisionColor, decisionIcon);
      showConfidence('decision', confidence);
    }

    // Update Alert Status
    if (data.alert) {
      const alert = data.alert.decision;
      const confidence = data.alert.confidence;
      
      const alertColor = alert === 'ALERT'
        ? { bg: '#fff7ed', fg: '#c2410c' }
        : { bg: '#f0f9ff', fg: '#075985' };
      const alertIcon = alert === 'ALERT' ? 'alert-triangle' : 'shield-check';
      
      setBadge('alertBadge', alert, alertColor, alertIcon);
      showConfidence('alert', confidence);
    }

    // Update Water Quantity with consistency check
    if (data.irrigation && data.irrigation.water_quantity) {
      let waterQuantity = data.irrigation.water_quantity;
      
      // Frontend consistency check: If irrigation is YES, water quantity should not be None
      if (data.irrigation.decision === 'YES' && waterQuantity === 'None') {
        console.warn('⚠️ Frontend consistency fix: Irrigation=YES but Water=None, fixing to Low');
        waterQuantity = 'Low';  // Override inconsistent data
      }
      
      let waterColor, waterIcon;
      
      switch(waterQuantity) {
        case 'High':
          waterColor = { bg: '#fef2f2', fg: '#b91c1c' };
          waterIcon = 'droplets';
          break;
        case 'Medium':
          waterColor = { bg: '#fefce8', fg: '#ca8a04' };
          waterIcon = 'droplet';
          break;
        case 'Low':
          waterColor = { bg: '#f0f9ff', fg: '#0369a1' };
          waterIcon = 'droplet';
          break;
        default:
          waterColor = { bg: '#f8fafc', fg: '#64748b' };
          waterIcon = 'droplet-off';
      }
      
      setBadge('waterQuantityBadge', waterQuantity, waterColor, waterIcon);
    } else if (data.irrigation && data.irrigation.decision === 'YES') {
      // Additional safeguard: If irrigation is YES but no water_quantity provided, set to Low
      console.warn('⚠️ Frontend safeguard: Irrigation=YES but no water quantity provided, setting to Low');
      setBadge('waterQuantityBadge', 'Low', { bg: '#f0f9ff', fg: '#0369a1' }, 'droplet');
    }

    // Update explanation
    updateExplanation(data);
    
    // Show recommended action
    const waterQuantity = data.irrigation && data.irrigation.water_quantity ? data.irrigation.water_quantity : null;
    showRecommendation(data.irrigation.decision, data.alert.decision, reqPayload, waterQuantity);
    
    // Update trends based on current data
    updateTrends(reqPayload);
    
    // Update system status
    updateSystemStatus('Inference Complete');

  } catch (e) {
    console.error('Error:', e);
    setBadge('decisionBadge', 'Error', { bg: '#fef2f2', fg: '#b91c1c' }, 'x-circle');
    setBadge('alertBadge', 'Error', { bg: '#fff7ed', fg: '#c2410c' }, 'alert-triangle');
    alert('Server error. Please ensure models are trained and try again.');
  } finally {
    // Restore button
    btn.disabled = false;
    btn.innerHTML = originalText;
  }
});

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
  renderPayload();
  setBadge('decisionBadge', 'Pending', { bg: '#f8fafc', fg: '#0f172a' }, 'help-circle');
  setBadge('alertBadge', 'NORMAL', { bg: '#f0f9ff', fg: '#075985' }, 'shield-check');
  setBadge('waterQuantityBadge', 'None', { bg: '#f8fafc', fg: '#64748b' }, 'droplet-off');
  updateSystemStatus('Ready');
  updateTrends(payload());
  console.log('🌱 Smart Irrigation System initialized');
});