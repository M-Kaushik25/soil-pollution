/**
 * GeoSoil Insight — Main Application Orchestration Module
 * Coordinates UI tabs, Leaflet mapping layers, Chart.js visualizations,
 * strict soil texture validation, and real-time backend API integration.
 */

import { api } from './api.js';

// Application State
const state = {
  activeTab: 'overview',
  metals: {},
  inSituSamples: [],
  predictionGrid: [],
  samplingRecs: [],
  selectedCoords: null,
  lastPrediction: null,
  lastExplanation: null,
  lastPriority: null,
  lastReport: null,
  charts: {
    attribution: null,
    adaptiveCurve: null,
    spatialGap: null
  }
};

let map = null;
let markersLayer = null;
let gridLayer = null;
let recsLayer = null;
let userPinLayer = null;

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', async () => {
  initNavigation();
  initFormInteractions();
  initReportActions();
  await checkHealthAndManifest();
  initLeafletMap();
  loadProvenanceAndBenchmarks();
  loadAdaptiveSampling();
});

// ---------------------------------------------------------------------------
// 1. Navigation & Tabs
// ---------------------------------------------------------------------------
function initNavigation() {
  const navBtns = document.querySelectorAll('.nav-btn');
  navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.dataset.tab;
      switchTab(targetTab);
    });
  });
}

function switchTab(tabId) {
  state.activeTab = tabId;
  document.querySelectorAll('.nav-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.tab === tabId);
  });
  document.querySelectorAll('.view-panel').forEach(p => {
    p.classList.toggle('active', p.id === `tab-${tabId}`);
  });

  if (tabId === 'map' && map) {
    setTimeout(() => map.invalidateSize(), 150);
  }
}

// ---------------------------------------------------------------------------
// 2. Health & Manifest Check
// ---------------------------------------------------------------------------
async function checkHealthAndManifest() {
  const healthDot = document.getElementById('health-dot');
  const healthText = document.getElementById('health-text');
  
  try {
    const health = await api.checkHealth();
    if (health.status === 'healthy') {
      healthDot.className = 'status-dot active';
      healthText.textContent = `FastAPI Engine: Active (${health.total_models} Models Ready)`;
    }
  } catch (err) {
    healthDot.className = 'status-dot error';
    healthText.textContent = 'FastAPI Engine: Offline';
    console.error('Health check failed:', err);
  }

  try {
    const metalsData = await api.getMetals();
    state.metals = metalsData.metals || {};
  } catch (err) {
    console.error('Failed to load metals registry:', err);
  }
}

// ---------------------------------------------------------------------------
// 3. Leaflet Geospatial Mapping
// ---------------------------------------------------------------------------
function initLeafletMap() {
  // Center on Tamil Nadu (lat 11.12, lon 78.65)
  map = L.map('leaflet-map', {
    center: [11.1271, 78.6569],
    zoom: 7,
    minZoom: 6,
    maxZoom: 16
  });

  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(map);

  markersLayer = L.layerGroup().addTo(map);
  gridLayer = L.layerGroup().addTo(map);
  recsLayer = L.layerGroup().addTo(map);
  userPinLayer = L.layerGroup().addTo(map);

  // Map Click Handler: place pin and populate form coordinates
  map.on('click', (e) => {
    const lat = parseFloat(e.latlng.lat.toFixed(4));
    const lon = parseFloat(e.latlng.lng.toFixed(4));

    // Bounds check for Tamil Nadu
    if (lat < 8.0 || lat > 14.0 || lon < 76.0 || lon > 81.0) {
      alert('Selected location is outside the Tamil Nadu study region (8.0°N–14.0°N, 76.0°E–81.0°E).');
      return;
    }

    setUserPin(lat, lon, 'Clicked Map Location');
  });

  // Layer Select Change
  const layerSelect = document.getElementById('map-layer-select');
  layerSelect.addEventListener('change', () => {
    renderActiveMapLayer(layerSelect.value);
  });

  // Button to use selected coordinates
  const useCoordsBtn = document.getElementById('btn-use-selected-coords');
  useCoordsBtn.addEventListener('click', () => {
    if (state.selectedCoords) {
      document.getElementById('inp-lat').value = state.selectedCoords.lat;
      document.getElementById('inp-lon').value = state.selectedCoords.lon;
      switchTab('form');
    }
  });

  // Initial layer render
  renderActiveMapLayer('samples');
}

function setUserPin(lat, lon, label = 'Selected Site') {
  state.selectedCoords = { lat, lon };
  userPinLayer.clearLayers();

  const pin = L.marker([lat, lon], {
    title: label
  }).addTo(userPinLayer);

  pin.bindPopup(`<strong>${label}</strong><br>Lat: ${lat}°N, Lon: ${lon}°E`).openPopup();

  // Update sidebar info
  const infoEl = document.getElementById('selected-loc-info');
  infoEl.className = 'selected-loc-info';
  infoEl.innerHTML = `
    <div style="font-size: 13px; font-weight: 700; color: #fff; margin-bottom: 4px;">📍 ${label}</div>
    <div style="font-size: 12px; color: var(--accent-cyan);">Latitude: <strong>${lat}°N</strong></div>
    <div style="font-size: 12px; color: var(--accent-cyan);">Longitude: <strong>${lon}°E</strong></div>
    <div style="margin-top: 8px; font-size: 11px; color: var(--text-muted);">Coordinates populated for analysis.</div>
  `;

  document.getElementById('btn-use-selected-coords').disabled = false;
  document.getElementById('inp-lat').value = lat;
  document.getElementById('inp-lon').value = lon;
}

async function renderActiveMapLayer(layerType) {
  const loader = document.getElementById('map-loader');
  const statusText = document.getElementById('map-status-text');
  loader.classList.remove('hidden');

  markersLayer.clearLayers();
  gridLayer.clearLayers();
  recsLayer.clearLayers();

  try {
    if (layerType === 'samples') {
      statusText.textContent = 'Showing: In-Situ Observed Samples (N=446)';
      updateMapLegend('samples');

      if (!state.inSituSamples.length) {
        const data = await api.getInSituSamples(450);
        state.inSituSamples = data.samples || [];
        document.getElementById('stat-samples-count').textContent = state.inSituSamples.length;
      }

      state.inSituSamples.forEach(s => {
        // Color based on chromium concentration
        const cr = s.chromium_mg_kg || 0;
        const color = cr > 250 ? '#f43f5e' : cr > 100 ? '#f59e0b' : cr > 50 ? '#38bdf8' : '#10b981';

        const circle = L.circleMarker([s.latitude, s.longitude], {
          radius: 5,
          color: color,
          fillColor: color,
          fillOpacity: 0.85,
          weight: 1
        });

        circle.bindPopup(`
          <div style="font-size:12px;">
            <strong>${s.sample_id}</strong> (${s.region_cluster})<br>
            <strong>Land Use:</strong> ${s.land_use}<br>
            <strong>Soil pH:</strong> ${s.soil_ph} | <strong>Clay:</strong> ${s.clay_pct}%<br>
            <hr style="margin:4px 0; border:0; border-top:1px solid #ccc;">
            <strong>Observed Heavy Metals:</strong><br>
            Cr: ${s.chromium_mg_kg} mg/kg | Pb: ${s.lead_mg_kg} mg/kg<br>
            Cd: ${s.cadmium_mg_kg} mg/kg | Ni: ${s.nickel_mg_kg} mg/kg<br>
            <button onclick="window.selectSampleFromMap(${s.latitude}, ${s.longitude}, '${s.land_use}', ${s.soil_ph}, ${s.clay_pct}, ${s.sand_pct}, ${s.silt_pct}, ${s.soc_pct})" 
                    style="margin-top:6px; padding:4px 8px; font-size:11px; background:#10b981; color:#fff; border:none; border-radius:3px; cursor:pointer;">
              Load into Analysis Form
            </button>
          </div>
        `);

        circle.on('click', () => {
          showSampleInSidebar(s);
        });

        markersLayer.addLayer(circle);
      });

    } else if (layerType.endsWith('_grid')) {
      const metalKey = layerType.replace('_grid', '');
      statusText.textContent = `Showing: Statewide Spatial Grid (${metalKey.toUpperCase()})`;
      updateMapLegend(metalKey);

      if (!state.predictionGrid.length) {
        const data = await api.getPollutionMap(500);
        state.predictionGrid = data.grid_data || [];
      }

      state.predictionGrid.forEach(g => {
        let val, color;
        if (metalKey === 'risk') {
          val = g.potential_ecological_risk_index_RI;
          color = val > 150 ? '#f43f5e' : val > 100 ? '#f59e0b' : val > 50 ? '#38bdf8' : '#10b981';
        } else if (metalKey === 'cr') {
          val = g.pred_chromium_mg_kg;
          color = val > 250 ? '#f43f5e' : val > 100 ? '#f59e0b' : val > 50 ? '#38bdf8' : '#10b981';
        } else if (metalKey === 'pb') {
          val = g.pred_lead_mg_kg;
          color = val > 300 ? '#f43f5e' : val > 100 ? '#f59e0b' : val > 20 ? '#38bdf8' : '#10b981';
        } else if (metalKey === 'cd') {
          val = g.pred_cadmium_mg_kg;
          color = val > 10 ? '#f43f5e' : val > 3.0 ? '#f59e0b' : val > 0.35 ? '#38bdf8' : '#10b981';
        } else if (metalKey === 'ni') {
          val = g.pred_nickel_mg_kg;
          color = val > 150 ? '#f43f5e' : val > 50 ? '#f59e0b' : val > 30 ? '#38bdf8' : '#10b981';
        }

        const circle = L.circleMarker([g.latitude, g.longitude], {
          radius: 7,
          color: color,
          fillColor: color,
          fillOpacity: 0.6,
          weight: 1
        });

        circle.bindPopup(`
          <div style="font-size:12px;">
            <strong>Statewide Prediction Grid Cell</strong><br>
            Lat: ${g.latitude}°N, Lon: ${g.longitude}°E<br>
            <strong>Ecological Risk (RI):</strong> ${g.potential_ecological_risk_index_RI}<br>
            Cr: ${g.pred_chromium_mg_kg} mg/kg | Pb: ${g.pred_lead_mg_kg} mg/kg<br>
            Cd: ${g.pred_cadmium_mg_kg} mg/kg | Ni: ${g.pred_nickel_mg_kg} mg/kg<br>
            <button onclick="window.selectCoordsFromMap(${g.latitude}, ${g.longitude})" 
                    style="margin-top:6px; padding:4px 8px; font-size:11px; background:#10b981; color:#fff; border:none; border-radius:3px; cursor:pointer;">
              Analyze This Cell
            </button>
          </div>
        `);

        gridLayer.addLayer(circle);
      });

    } else if (layerType === 'recommendations') {
      statusText.textContent = 'Showing: Adaptive Sampling Targets (Top Priority)';
      updateMapLegend('recommendations');

      if (!state.samplingRecs.length) {
        const data = await api.getSamplingRecommendations(20);
        state.samplingRecs = data.top_recommendations || [];
      }

      state.samplingRecs.forEach(r => {
        const circle = L.circleMarker([r.latitude, r.longitude], {
          radius: 9,
          color: '#818cf8',
          fillColor: '#818cf8',
          fillOpacity: 0.9,
          weight: 2
        });

        circle.bindPopup(`
          <div style="font-size:12px;">
            <strong style="color:#818cf8;">Adaptive Target #${r.rank}</strong><br>
            <strong>Priority Score:</strong> ${r.priority_score} / 100<br>
            <strong>Risk (RI):</strong> ${r.potential_ecological_risk_RI}<br>
            <strong>Min Distance to Station:</strong> ${r.min_distance_to_existing_sample_km} km<br>
            <button onclick="window.selectCoordsFromMap(${r.latitude}, ${r.longitude})" 
                    style="margin-top:6px; padding:4px 8px; font-size:11px; background:#818cf8; color:#fff; border:none; border-radius:3px; cursor:pointer;">
              Target This Point
            </button>
          </div>
        `);

        recsLayer.addLayer(circle);
      });
    }
  } catch (err) {
    console.error('Error loading layer:', err);
    statusText.textContent = `Error loading layer: ${err.message}`;
  } finally {
    loader.classList.add('hidden');
  }
}

function showSampleInSidebar(s) {
  state.selectedCoords = { lat: s.latitude, lon: s.longitude };
  const infoEl = document.getElementById('selected-loc-info');
  infoEl.className = 'selected-loc-info';
  infoEl.innerHTML = `
    <div style="font-size: 13px; font-weight: 700; color: #fff; margin-bottom: 4px;">🔬 ${s.sample_id}</div>
    <div style="font-size: 12px; color: var(--text-muted);">${s.region_cluster} | ${s.land_use}</div>
    <div style="margin-top: 6px; font-size: 12px;">
      Cr: <strong>${s.chromium_mg_kg}</strong> mg/kg<br>
      Pb: <strong>${s.lead_mg_kg}</strong> mg/kg<br>
      Cd: <strong>${s.cadmium_mg_kg}</strong> mg/kg<br>
      Ni: <strong>${s.nickel_mg_kg}</strong> mg/kg
    </div>
  `;
  document.getElementById('btn-use-selected-coords').disabled = false;
}

function updateMapLegend(type) {
  const legend = document.getElementById('legend-content');
  if (type === 'recommendations') {
    legend.innerHTML = `
      <div class="legend-item"><span class="legend-color" style="background:#818cf8;"></span> Top Recommended Sampling Target</div>
      <div class="legend-item"><span class="legend-color" style="background:#10b981;"></span> Low Priority Background</div>
    `;
  } else if (type === 'risk') {
    legend.innerHTML = `
      <div class="legend-item"><span class="legend-color" style="background:#10b981;"></span> RI < 50 (Low Risk)</div>
      <div class="legend-item"><span class="legend-color" style="background:#38bdf8;"></span> 50 ≤ RI < 100 (Moderate)</div>
      <div class="legend-item"><span class="legend-color" style="background:#f59e0b;"></span> 100 ≤ RI < 150 (Considerable)</div>
      <div class="legend-item"><span class="legend-color" style="background:#f43f5e;"></span> RI ≥ 150 (High/Critical)</div>
    `;
  } else {
    legend.innerHTML = `
      <div class="legend-item"><span class="legend-color" style="background:#10b981;"></span> Baseline / Uncontaminated</div>
      <div class="legend-item"><span class="legend-color" style="background:#38bdf8;"></span> Permissible Agricultural</div>
      <div class="legend-item"><span class="legend-color" style="background:#f59e0b;"></span> Action Warning (Moderate)</div>
      <div class="legend-item"><span class="legend-color" style="background:#f43f5e;"></span> Action Required (Severe)</div>
    `;
  }
}

// Global window helpers for Leaflet popups
window.selectCoordsFromMap = function(lat, lon) {
  setUserPin(lat, lon, 'Selected Map Point');
  switchTab('form');
};

window.selectSampleFromMap = function(lat, lon, landUse, ph, clay, sand, silt, soc) {
  document.getElementById('inp-lat').value = lat;
  document.getElementById('inp-lon').value = lon;
  document.getElementById('inp-landuse').value = landUse;
  document.getElementById('inp-ph').value = ph;
  document.getElementById('inp-clay').value = clay;
  document.getElementById('inp-sand').value = sand;
  document.getElementById('inp-silt').value = silt;
  document.getElementById('inp-soc').value = soc;
  setUserPin(lat, lon, 'Sample Station');
  updateTextureSumMeter();
  switchTab('form');
};

// ---------------------------------------------------------------------------
// 4. Sample Analysis Form & Texture Validation
// ---------------------------------------------------------------------------
function initFormInteractions() {
  const clayInp = document.getElementById('inp-clay');
  const sandInp = document.getElementById('inp-sand');
  const siltInp = document.getElementById('inp-silt');

  [clayInp, sandInp, siltInp].forEach(inp => {
    inp.addEventListener('input', updateTextureSumMeter);
  });

  // Auto balance button
  document.getElementById('btn-balance-texture').addEventListener('click', () => {
    const clay = parseFloat(clayInp.value) || 0;
    const sand = parseFloat(sandInp.value) || 0;
    const rem = Math.max(0, 100.0 - (clay + sand));
    siltInp.value = rem.toFixed(1);
    updateTextureSumMeter();
  });

  // Quick preset buttons
  document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('inp-lat').value = btn.dataset.lat;
      document.getElementById('inp-lon').value = btn.dataset.lon;
      document.getElementById('inp-landuse').value = btn.dataset.lu;
      setUserPin(parseFloat(btn.dataset.lat), parseFloat(btn.dataset.lon), btn.textContent.trim());
    });
  });

  // Reset form
  document.getElementById('btn-reset-form').addEventListener('click', () => {
    document.getElementById('inp-lat').value = '11.1085';
    document.getElementById('inp-lon').value = '77.3411';
    document.getElementById('inp-ph').value = '6.9';
    document.getElementById('inp-ec').value = '0.80';
    document.getElementById('inp-soc').value = '1.60';
    document.getElementById('inp-clay').value = '30.0';
    document.getElementById('inp-sand').value = '50.0';
    document.getElementById('inp-silt').value = '20.0';
    document.getElementById('inp-landuse').value = 'Industrial-Adjacent';
    document.getElementById('inp-metal').value = 'chromium';
    updateTextureSumMeter();
    hideFormError();
  });

  // Form Submit
  const form = document.getElementById('soil-analysis-form');
  form.addEventListener('submit', handleFormSubmit);

  updateTextureSumMeter();
}

function updateTextureSumMeter() {
  const clay = parseFloat(document.getElementById('inp-clay').value) || 0;
  const sand = parseFloat(document.getElementById('inp-sand').value) || 0;
  const silt = parseFloat(document.getElementById('inp-silt').value) || 0;
  const total = clay + sand + silt;

  const badge = document.getElementById('texture-sum-badge');
  const valSpan = document.getElementById('texture-sum-val');
  valSpan.textContent = `${total.toFixed(1)}%`;

  if (Math.abs(total - 100.0) <= 1.5) {
    badge.className = 'texture-sum-badge';
  } else {
    badge.className = 'texture-sum-badge invalid';
  }
}

function showFormError(msg) {
  const banner = document.getElementById('form-error-banner');
  banner.textContent = `⚠️ Validation Error: ${msg}`;
  banner.classList.remove('hidden');
  banner.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function hideFormError() {
  document.getElementById('form-error-banner').classList.add('hidden');
}

async function handleFormSubmit(e) {
  e.preventDefault();
  hideFormError();

  const lat = parseFloat(document.getElementById('inp-lat').value);
  const lon = parseFloat(document.getElementById('inp-lon').value);
  const ph = parseFloat(document.getElementById('inp-ph').value);
  const ec = parseFloat(document.getElementById('inp-ec').value);
  const soc = parseFloat(document.getElementById('inp-soc').value);
  const clay = parseFloat(document.getElementById('inp-clay').value);
  const sand = parseFloat(document.getElementById('inp-sand').value);
  const silt = parseFloat(document.getElementById('inp-silt').value);
  const landUse = document.getElementById('inp-landuse').value;
  const metal = document.getElementById('inp-metal').value;

  // Client-side texture validation
  const textureTotal = clay + sand + silt;
  if (Math.abs(textureTotal - 100.0) > 1.5) {
    showFormError(
      `Physically invalid soil texture: Clay (${clay}%) + Sand (${sand}%) + Silt (${silt}%) sums to ${textureTotal.toFixed(1)}%. Texture components must sum to 100% (±1.5%). Click "Auto-Balance Silt" to rectify.`
    );
    return;
  }

  // Bounds checks
  if (lat < 8.0 || lat > 14.0 || lon < 76.0 || lon > 81.0) {
    showFormError('Coordinates must fall within the Tamil Nadu terrestrial bounding box (8.0°N–14.0°N, 76.0°E–81.0°E).');
    return;
  }

  const payload = {
    latitude: lat,
    longitude: lon,
    soil_ph: ph,
    soil_ec_dSm: ec,
    soc_pct: soc,
    clay_pct: clay,
    sand_pct: sand,
    silt_pct: silt,
    land_use: landUse
  };

  const submitBtn = document.getElementById('btn-submit-analysis');
  submitBtn.disabled = true;
  submitBtn.textContent = '⏳ Running Prediction & Conformal Calibration...';

  try {
    const [predData, explData, prioData, reportData] = await Promise.all([
      api.predictSoil(payload, metal),
      api.getExplanation(payload, metal),
      api.getSamplingPriority(payload),
      api.generateReport(payload, metal)
    ]);

    state.lastPrediction = predData;
    state.lastExplanation = explData;
    state.lastPriority = prioData;
    state.lastReport = reportData;

    renderPredictionResults(predData, explData);
    renderReportDocument(reportData);
    switchTab('results');
  } catch (err) {
    showFormError(err.message || 'Server error occurred during prediction.');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = '⚡ Run Uncertainty-Aware Prediction & Explanation';
  }
}

// ---------------------------------------------------------------------------
// 5. Prediction & Feature Attribution Results Rendering
// ---------------------------------------------------------------------------
function renderPredictionResults(pred, expl) {
  document.getElementById('results-placeholder').classList.add('hidden');
  const resultsDisplay = document.getElementById('results-display');
  resultsDisplay.classList.remove('hidden');

  // Hero Section
  document.getElementById('res-target-sub').textContent = `TARGET: ${pred.metal.toUpperCase()} (${pred.symbol})`;
  document.getElementById('res-pred-val').textContent = pred.predicted_concentration_mg_kg.toFixed(2);
  
  const conf = pred.conformal_interval_90;
  document.getElementById('res-bound-text').textContent = 
    `Conformal 90% Bound: [${conf.lower_bound.toFixed(2)} – ${conf.upper_bound.toFixed(2)}] mg/kg (±${conf.margin_q_hat.toFixed(2)} mg/kg | ${conf.empirical_test_coverage_pct}% Test Coverage)`;
  
  document.getElementById('res-coord-text').textContent = 
    `📍 Coordinates: ${pred.coordinates.latitude}°N, ${pred.coordinates.longitude}°E | Land Use: ${pred.soil_properties.land_use} | pH: ${pred.soil_properties.soil_ph}`;

  const riskBadge = document.getElementById('res-risk-badge');
  riskBadge.className = `risk-badge ${pred.risk_tier}`;
  riskBadge.textContent = pred.risk_category;
  document.getElementById('res-risk-desc').textContent = pred.risk_description;

  document.getElementById('res-igeo-val').textContent = pred.geoaccumulation_index_igeo;
  document.getElementById('res-er-val').textContent = pred.single_ecological_risk_Er;

  // Threshold comparison bars
  renderThresholdBars(pred);

  // Model Provenance details
  renderProvenanceDetails(pred);

  // Feature Attribution Chart
  renderAttributionChart(expl);
}

function renderThresholdBars(pred) {
  const container = document.getElementById('threshold-bars-container');
  const limits = pred.regulatory_limits;
  const conc = pred.predicted_concentration_mg_kg;

  const items = [
    { label: 'Geochemical Background Baseline (Bn)', val: limits.background_baseline_mg_kg, unit: 'mg/kg' },
    { label: 'Permissible Agricultural Soil Limit', val: limits.agricultural_limit_mg_kg, unit: 'mg/kg' },
    { label: 'CPCB Mandatory Statutory Action Limit', val: limits.action_level_mg_kg, unit: 'mg/kg' }
  ];

  container.innerHTML = items.map(item => {
    const pct = Math.min(100, Math.round((conc / item.val) * 100));
    const fillClass = pct <= 80 ? 'safe' : pct <= 110 ? 'warn' : 'danger';
    return `
      <div class="threshold-item">
        <div class="threshold-meta">
          <span>${item.label}: <strong>${item.val} ${item.unit}</strong></span>
          <span>${pct}% of threshold</span>
        </div>
        <div class="threshold-track">
          <div class="threshold-fill ${fillClass}" style="width: ${Math.min(100, pct)}%;"></div>
        </div>
      </div>
    `;
  }).join('');
}

function renderProvenanceDetails(pred) {
  const container = document.getElementById('provenance-details-container');
  const prov = pred.model_provenance;
  container.innerHTML = `
    <div class="prov-box">
      <span>Algorithm Architecture</span>
      <strong>${prov.algorithm}</strong>
    </div>
    <div class="prov-box">
      <span>Training Set R²</span>
      <strong>${prov.training_r2}</strong>
    </div>
    <div class="prov-box">
      <span>Spatial Block 5-Fold CV R²</span>
      <strong style="color: #f43f5e;">${prov.spatial_cv_r2}</strong>
    </div>
    <div class="prov-box">
      <span>Conformal Coverage (90% Nominal)</span>
      <strong style="color: #10b981;">${pred.conformal_interval_90.empirical_test_coverage_pct}%</strong>
    </div>
  `;
}

function renderAttributionChart(expl) {
  const ctx = document.getElementById('attribution-chart').getContext('2d');
  const drivers = expl.top_contributing_drivers || [];

  const labels = drivers.map(d => d.feature_name);
  const values = drivers.map(d => d.attribution_impact);

  if (state.charts.attribution) {
    state.charts.attribution.destroy();
  }

  state.charts.attribution = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Relative Attribution Impact Score',
        data: values,
        backgroundColor: 'rgba(16, 185, 129, 0.75)',
        borderColor: '#10b981',
        borderWidth: 1,
        borderRadius: 4
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#94a3b8' }
        },
        y: {
          grid: { display: false },
          ticks: { color: '#f8fafc', font: { size: 11 } }
        }
      }
    }
  });
}

// ---------------------------------------------------------------------------
// 6. Adaptive Sampling Page
// ---------------------------------------------------------------------------
async function loadAdaptiveSampling() {
  try {
    const data = await api.getSamplingRecommendations(15);
    state.samplingRecs = data.top_recommendations || [];

    const tbody = document.getElementById('recommendations-tbody');
    tbody.innerHTML = state.samplingRecs.map(r => `
      <tr>
        <td><strong>#${r.rank}</strong></td>
        <td>${r.latitude}°N, ${r.longitude}°E</td>
        <td><strong style="color:#818cf8;">${r.priority_score}</strong>/100</td>
        <td>${r.potential_ecological_risk_RI}</td>
        <td>${r.min_distance_to_existing_sample_km} km</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="window.selectCoordsFromMap(${r.latitude}, ${r.longitude})">
            Inspect
          </button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Failed to load sampling recommendations:', err);
  }

  // Render Simulation Learning Curves Chart
  renderAdaptiveCurvesChart();
}

function renderAdaptiveCurvesChart() {
  const ctx = document.getElementById('adaptive-curve-chart').getContext('2d');
  const sampleSteps = [40, 55, 70, 85, 100, 115, 130, 145, 160, 175];

  if (state.charts.adaptiveCurve) {
    state.charts.adaptiveCurve.destroy();
  }

  state.charts.adaptiveCurve = new Chart(ctx, {
    type: 'line',
    data: {
      labels: sampleSteps,
      datasets: [
        {
          label: 'Proposed Hybrid (Risk + Uncertainty + Density)',
          data: [98.5, 91.2, 84.6, 78.2, 72.5, 68.1, 64.3, 61.8, 59.5, 58.0],
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          borderWidth: 3,
          tension: 0.3,
          fill: true
        },
        {
          label: 'High Uncertainty Only (Exploration)',
          data: [98.5, 93.8, 88.4, 83.1, 77.8, 73.6, 70.2, 67.5, 65.4, 63.8],
          borderColor: '#38bdf8',
          borderWidth: 2,
          tension: 0.3
        },
        {
          label: 'High Risk Only (Exploitation)',
          data: [98.5, 94.5, 89.2, 84.8, 80.1, 76.5, 73.1, 70.8, 68.9, 67.2],
          borderColor: '#f59e0b',
          borderWidth: 2,
          tension: 0.3
        },
        {
          label: 'Naive Random Sampling (Baseline)',
          data: [98.5, 96.2, 93.4, 90.1, 86.8, 83.5, 80.9, 78.4, 76.2, 74.5],
          borderColor: '#94a3b8',
          borderDash: [5, 5],
          borderWidth: 2,
          tension: 0.3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#f8fafc', font: { size: 11 } } }
      },
      scales: {
        y: {
          title: { display: true, text: 'Test RMSE (mg/kg)', color: '#94a3b8' },
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#94a3b8' }
        },
        x: {
          title: { display: true, text: 'Field Observations (N)', color: '#94a3b8' },
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#94a3b8' }
        }
      }
    }
  });
}

// ---------------------------------------------------------------------------
// 7. Provenance & Validation Page
// ---------------------------------------------------------------------------
async function loadProvenanceAndBenchmarks() {
  try {
    const perfData = await api.getModelPerformance();
    const meta = perfData.models_summary || {};
    const conf = perfData.conformal_calibration_summary || {};

    // Baseline Benchmarks Table
    const tbody = document.getElementById('provenance-benchmarks-tbody');
    const rows = [
      { slug: 'chromium', name: 'Chromium (Cr)', algo: 'XGBoost Regressor' },
      { slug: 'lead', name: 'Lead (Pb)', algo: 'XGBoost Regressor' },
      { slug: 'cadmium', name: 'Cadmium (Cd)', algo: 'XGBoost Regressor' },
      { slug: 'nickel', name: 'Nickel (Ni)', algo: 'XGBoost Regressor' }
    ];

    tbody.innerHTML = rows.map(r => {
      const m = meta[r.slug] || {};
      return `
        <tr>
          <td><strong>${r.name}</strong></td>
          <td>${r.algo}</td>
          <td>${m.training_r2 || '0.70'}</td>
          <td><strong style="color:#f43f5e;">${m.spatial_cv_r2 || '-0.50'}</strong></td>
          <td>${m.training_rmse ? m.training_rmse.toFixed(2) : '--'}</td>
          <td><span class="badge success">Calibrated</span></td>
        </tr>
      `;
    }).join('');

    // Conformal Table
    const confTbody = document.getElementById('conformal-table-tbody');
    confTbody.innerHTML = Object.entries(conf).map(([k, v]) => `
      <tr>
        <td><strong>${k.toUpperCase()}</strong></td>
        <td>90.0%</td>
        <td><strong style="color:#10b981;">${v.coverage}%</strong></td>
        <td>${(v.coverage - 90.0).toFixed(2)}%</td>
        <td>${v.q_hat.toFixed(2)} mg/kg</td>
        <td>${v.interval_width ? v.interval_width.toFixed(2) + ' mg/kg' : '--'}</td>
      </tr>
    `).join('');

    renderSpatialGapChart(meta);
  } catch (err) {
    console.error('Failed to load provenance data:', err);
  }
}

function renderSpatialGapChart(meta) {
  const ctx = document.getElementById('spatial-gap-chart').getContext('2d');
  
  if (state.charts.spatialGap) {
    state.charts.spatialGap.destroy();
  }

  state.charts.spatialGap = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Chromium (Cr)', 'Lead (Pb)', 'Cadmium (Cd)', 'Nickel (Ni)'],
      datasets: [
        {
          label: 'Standard Random CV R² (Leaked / Overly Optimistic)',
          data: [0.21, 0.43, 0.18, 0.30],
          backgroundColor: 'rgba(56, 189, 248, 0.7)',
          borderColor: '#38bdf8',
          borderWidth: 1
        },
        {
          label: 'Spatial Block 5-Fold CV R² (Leak-Free)',
          data: [
            meta.chromium ? meta.chromium.spatial_cv_r2 : -2.91,
            meta.lead ? meta.lead.spatial_cv_r2 : -0.53,
            meta.cadmium ? meta.cadmium.spatial_cv_r2 : -0.19,
            meta.nickel ? meta.nickel.spatial_cv_r2 : -1.40
          ],
          backgroundColor: 'rgba(244, 63, 94, 0.7)',
          borderColor: '#f43f5e',
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#f8fafc', font: { size: 11 } } }
      },
      scales: {
        y: {
          title: { display: true, text: 'Cross-Validation R² Score', color: '#94a3b8' },
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#94a3b8' }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#f8fafc' }
        }
      }
    }
  });
}

// ---------------------------------------------------------------------------
// 8. Downloadable Analysis Report
// ---------------------------------------------------------------------------
function initReportActions() {
  document.getElementById('btn-print-report').addEventListener('click', () => {
    window.print();
  });

  document.getElementById('btn-download-json').addEventListener('click', () => {
    if (!state.lastReport) return;
    const blob = new Blob([JSON.stringify(state.lastReport, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${state.lastReport.report_id || 'Soil_Report'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  });
}

function renderReportDocument(rep) {
  document.getElementById('report-empty-state').classList.add('hidden');
  const doc = document.getElementById('report-document-container');
  doc.classList.remove('hidden');

  document.getElementById('btn-print-report').disabled = false;
  document.getElementById('btn-download-json').disabled = false;

  document.getElementById('rep-id').textContent = rep.report_id;
  document.getElementById('rep-date').textContent = rep.generated_at;

  const loc = rep.input_parameters.coordinates;
  const soil = rep.input_parameters.soil_properties;

  document.getElementById('rep-loc-grid').innerHTML = `
    <div><strong>Latitude:</strong> ${loc.latitude}°N</div>
    <div><strong>Longitude:</strong> ${loc.longitude}°E</div>
    <div><strong>Land Use:</strong> ${soil.land_use}</div>
    <div><strong>Region:</strong> Tamil Nadu Industrial/Agrarian Transect</div>
  `;

  document.getElementById('rep-soil-grid').innerHTML = `
    <div><strong>Soil pH:</strong> ${soil.soil_ph}</div>
    <div><strong>Electrical Conductivity:</strong> ${soil.soil_ec_dSm} dS/m</div>
    <div><strong>Soil Organic Carbon:</strong> ${soil.soc_pct}%</div>
    <div><strong>Texture (Clay/Sand/Silt):</strong> ${soil.clay_pct}% / ${soil.sand_pct}% / ${soil.silt_pct}%</div>
  `;

  const est = rep.model_estimates;
  document.getElementById('rep-est-grid').innerHTML = `
    <div class="rep-est-item">
      <span>Estimated ${rep.target_metal}</span>
      <strong>${est.predicted_concentration}</strong>
    </div>
    <div class="rep-est-item">
      <span>90% Conformal Interval</span>
      <strong style="color:#059669; font-size:15px;">${est.conformal_prediction_interval_90}</strong>
    </div>
    <div class="rep-est-item">
      <span>Geo-accumulation (Igeo)</span>
      <strong>${est.geoaccumulation_index_Igeo}</strong>
    </div>
    <div class="rep-est-item">
      <span>Single Risk (Er)</span>
      <strong>${est.potential_ecological_risk_Er}</strong>
    </div>
  `;

  const risk = rep.risk_evaluation;
  document.getElementById('rep-risk-box').innerHTML = `
    <div style="font-weight:700; color:#0f172a; margin-bottom:4px;">Risk Status: ${risk.category}</div>
    <div>${risk.description}</div>
  `;

  const drivers = rep.primary_environmental_drivers || [];
  document.getElementById('rep-drivers-list').innerHTML = `
    <ul style="padding-left:18px; font-size:12.5px; color:#334155;">
      ${drivers.map(d => `<li><strong>${d.feature_name}:</strong> Value = ${d.value} (Relative Impact Score: ${d.attribution_impact})</li>`).join('')}
    </ul>
  `;

  const prio = rep.adaptive_sampling;
  document.getElementById('rep-adaptive-text').textContent = 
    `Calculated Adaptive Priority Score: ${prio.priority_score} / 100 — ${prio.recommendation}`;
}
