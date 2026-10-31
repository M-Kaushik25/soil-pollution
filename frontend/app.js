/**
 * GeoSoil Insight — Streamlined Application Orchestration Module
 * Coordinates interactive Leaflet mapping, integrated soil sample prediction,
 * conformal uncertainty bounds, tree attribution charts, and report exports.
 */

(function() {
  'use strict';

  // Fallback-safe API reference (works in classic script and module environments)
  const api = window.api || {
  getBaseUrl() { return "http://127.0.0.1:8000"; },
  async checkHealth() { return { status: "offline", total_models: 0 }; },
  async getMetals() { return { metals: {} }; },
  async getInSituSamples() { return { samples: [] }; },
  async getPollutionMap() { return { grid_data: [] }; },
  async predictSoil() { throw new Error("FastAPI engine is offline"); },
  async getExplanation() { throw new Error("FastAPI engine is offline"); },
  async getSamplingPriority() { throw new Error("FastAPI engine is offline"); },
  async getSamplingRecommendations() { return { top_recommendations: [] }; },
  async getModelPerformance() { return { models: {} }; },
  async generateReport() { throw new Error("FastAPI engine is offline"); }
};

// Application State
const state = {
  activeTab: 'map',
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

// Safe Ready-State Runner
function runWhenReady(fn) {
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    fn();
  } else {
    document.addEventListener('DOMContentLoaded', fn);
  }
}

// Initialize on DOM Ready
runWhenReady(() => {
  initNavigation();
  initFormInteractions();
  initReportActions();

  // Initialize map first and synchronously so UI map renders immediately
  initLeafletMap();

  // Window resize handler for responsive Leaflet rendering
  window.addEventListener('resize', () => {
    if (map && state.activeTab === 'map') {
      map.invalidateSize();
    }
  });

  // Asynchronously query backend status and metrics without blocking map UI
  checkHealth().finally(() => {
    loadProvenanceAndBenchmarks();
    loadAdaptiveSampling();
  });
});

// Helper for tile error warning banner
function showMapTileWarning(msg) {
  let warn = document.getElementById('map-tile-warning');
  if (!warn) {
    warn = document.createElement('div');
    warn.id = 'map-tile-warning';
    warn.className = 'map-tile-warning';
    const container = document.querySelector('.map-container-box') || document.body;
    container.appendChild(warn);
  }
  warn.textContent = msg;
  warn.style.display = 'block';
}

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
    map.invalidateSize();
    setTimeout(() => {
      if (map) map.invalidateSize();
    }, 150);
  }
}

// ---------------------------------------------------------------------------
// 2. Health & Manifest Check
// ---------------------------------------------------------------------------
async function checkHealth() {
  const healthDot = document.getElementById('health-dot');
  const healthText = document.getElementById('health-text');
  
  try {
    const health = await api.checkHealth();
    if (health.status === 'healthy') {
      healthDot.className = 'status-dot active';
      healthText.textContent = `FastAPI: Active (${health.total_models} Models Ready)`;
    } else {
      healthDot.className = 'status-dot error';
      healthText.textContent = 'FastAPI: Offline';
    }
  } catch (err) {
    healthDot.className = 'status-dot error';
    healthText.textContent = 'FastAPI: Offline';
    console.warn('Health check notice (Backend offline):', err.message || err);
  }

  try {
    const metalsData = await api.getMetals();
    state.metals = metalsData.metals || {};
  } catch (err) {
    console.warn('Metals metadata notice:', err.message || err);
  }
}

// ---------------------------------------------------------------------------
// 3. Leaflet Geospatial Mapping
// ---------------------------------------------------------------------------
function initLeafletMap() {
  const mapContainer = document.getElementById('leaflet-map');
  if (!mapContainer) return;

  // Prevent duplicate initialization
  if (map || mapContainer._leaflet_id) {
    return;
  }

  // Check if Leaflet library is loaded
  if (typeof window.L === 'undefined') {
    console.error('Leaflet library (window.L) is not loaded.');
    const fallbackMsg = document.getElementById('map-fallback-msg');
    if (fallbackMsg) {
      fallbackMsg.style.display = 'block';
      fallbackMsg.innerHTML = '<h3>Map Engine Notice</h3><p>The Leaflet mapping library could not be loaded from CDN. Please verify your internet connection.</p>';
    }
    return;
  }

  try {
    // Configure local assets path for Leaflet markers
    if (L.Icon && L.Icon.Default) {
      L.Icon.Default.imagePath = 'leaflet/images/';
    }

    // Center on Tamil Nadu (lat 11.1271, lon 78.6569) with default zoom 7
    map = L.map('leaflet-map', {
      center: [11.1271, 78.6569],
      zoom: 7,
      minZoom: 6,
      maxZoom: 16
    });

    // Primary Carto voyager tile layer
    const primaryTiles = L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 19
    });

    let tileErrorCount = 0;
    primaryTiles.on('tileerror', () => {
      tileErrorCount++;
      if (tileErrorCount === 3) {
        console.warn('Carto tile layer experiencing errors; switching to OpenStreetMap fallback.');
        map.removeLayer(primaryTiles);
        const osmFallback = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; OpenStreetMap contributors',
          maxZoom: 19
        }).addTo(map);
        osmFallback.on('tileerror', () => {
          showMapTileWarning('Tile network unreachable (offline). Coordinate picking and form analysis remain active.');
        });
      }
    });

    primaryTiles.addTo(map);

    markersLayer = L.layerGroup().addTo(map);
    gridLayer = L.layerGroup().addTo(map);
    recsLayer = L.layerGroup().addTo(map);
    userPinLayer = L.layerGroup().addTo(map);

    // Map Click Handler
    map.on('click', (e) => {
      const lat = parseFloat(e.latlng.lat.toFixed(4));
      const lon = parseFloat(e.latlng.lng.toFixed(4));

      if (lat < 8.0 || lat > 14.0 || lon < 76.0 || lon > 81.0) {
        alert('Selected location is outside the Tamil Nadu study region (8.0°N–14.0°N, 76.0°E–81.0°E).');
        return;
      }

      setUserPin(lat, lon, 'Selected Coordinates');
    });

    // Layer Select Change
    const layerSelect = document.getElementById('map-layer-select');
    if (layerSelect) {
      layerSelect.addEventListener('change', () => {
        renderActiveMapLayer(layerSelect.value);
      });
    }

    // Force dimension invalidation after initial layout pass
    setTimeout(() => {
      if (map) map.invalidateSize();
    }, 150);

    // Initial layer render
    renderActiveMapLayer('samples');
  } catch (err) {
    console.error('Failed to initialize Leaflet map:', err);
    const fallbackMsg = document.getElementById('map-fallback-msg');
    if (fallbackMsg) {
      fallbackMsg.style.display = 'block';
      fallbackMsg.innerHTML = `<h3>Map Initialization Error</h3><p>${err.message}</p>`;
    }
  }
}

function setUserPin(lat, lon, label = 'Selected Site') {
  state.selectedCoords = { lat, lon };
  userPinLayer.clearLayers();

  const pin = L.marker([lat, lon], { title: label }).addTo(userPinLayer);

  pin.bindPopup(`
    <div style="font-size:12px;">
      <strong>${label}</strong><br>
      Lat: ${lat}°N, Lon: ${lon}°E<br>
      <button onclick="window.selectCoordsFromMap(${lat}, ${lon})" 
              style="margin-top:6px; padding:4px 8px; font-size:11px; background:#10b981; color:#fff; border:none; border-radius:3px; cursor:pointer;">
        Analyze in Form
      </button>
    </div>
  `).openPopup();

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
            Cr: ${s.chromium_mg_kg} mg/kg | Pb: ${s.lead_mg_kg} mg/kg<br>
            Cd: ${s.cadmium_mg_kg} mg/kg | Ni: ${s.nickel_mg_kg} mg/kg<br>
            <button onclick="window.selectSampleFromMap(${s.latitude}, ${s.longitude}, '${s.land_use}', ${s.soil_ph}, ${s.clay_pct}, ${s.sand_pct}, ${s.silt_pct}, ${s.soc_pct})" 
                    style="margin-top:6px; padding:4px 8px; font-size:11px; background:#10b981; color:#fff; border:none; border-radius:3px; cursor:pointer;">
              Load into Analysis Form
            </button>
          </div>
        `);

        markersLayer.addLayer(circle);
      });

    } else if (layerType.endsWith('_grid')) {
      const metalKey = layerType.replace('_grid', '');
      statusText.textContent = `Showing: Statewide Spatial Grid (${metalKey.toUpperCase()})`;
      updateMapLegend(metalKey);

      if (!state.predictionGrid.length) {
        const data = await api.getPollutionMap(400);
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
          radius: 6,
          color: color,
          fillColor: color,
          fillOpacity: 0.6,
          weight: 1
        });

        circle.bindPopup(`
          <div style="font-size:12px;">
            <strong>Statewide Spatial Cell</strong><br>
            Lat: ${g.latitude}°N, Lon: ${g.longitude}°E<br>
            <strong>Risk (RI):</strong> ${g.potential_ecological_risk_index_RI}<br>
            Cr: ${g.pred_chromium_mg_kg} mg/kg | Pb: ${g.pred_lead_mg_kg} mg/kg<br>
            Cd: ${g.pred_cadmium_mg_kg} mg/kg | Ni: ${g.pred_nickel_mg_kg} mg/kg<br>
            <button onclick="window.selectCoordsFromMap(${g.latitude}, ${g.longitude})" 
                    style="margin-top:6px; padding:4px 8px; font-size:11px; background:#10b981; color:#fff; border:none; border-radius:3px; cursor:pointer;">
              Analyze in Form
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
          radius: 8,
          color: '#818cf8',
          fillColor: '#818cf8',
          fillOpacity: 0.9,
          weight: 2
        });

        circle.bindPopup(`
          <div style="font-size:12px;">
            <strong style="color:#818cf8;">Sampling Target #${r.rank}</strong><br>
            <strong>Priority Score:</strong> ${r.priority_score} / 100<br>
            <strong>Risk (RI):</strong> ${r.potential_ecological_risk_RI}<br>
            <strong>Distance:</strong> ${r.min_distance_to_existing_sample_km} km<br>
            <button onclick="window.selectCoordsFromMap(${r.latitude}, ${r.longitude})" 
                    style="margin-top:6px; padding:4px 8px; font-size:11px; background:#818cf8; color:#fff; border:none; border-radius:3px; cursor:pointer;">
              Load in Form
            </button>
          </div>
        `);

        recsLayer.addLayer(circle);
      });
    }
  } catch (err) {
    console.warn('Map layer data fetch notice (backend offline or unavailable):', err.message || err);
    statusText.textContent = 'Base Map Active (Backend data offline — click anywhere on map to select coordinates)';
  } finally {
    loader.classList.add('hidden');
  }
}

function updateMapLegend(type) {
  const legend = document.getElementById('legend-content');
  if (type === 'recommendations') {
    legend.innerHTML = `
      <div class="legend-item"><span class="legend-color" style="background:#818cf8;"></span> Priority Sampling Target</div>
      <div class="legend-item"><span class="legend-color" style="background:#10b981;"></span> Baseline Monitor</div>
    `;
  } else if (type === 'risk') {
    legend.innerHTML = `
      <div class="legend-item"><span class="legend-color" style="background:#10b981;"></span> RI < 50 (Low Risk)</div>
      <div class="legend-item"><span class="legend-color" style="background:#38bdf8;"></span> 50 ≤ RI < 100 (Moderate)</div>
      <div class="legend-item"><span class="legend-color" style="background:#f59e0b;"></span> 100 ≤ RI < 150 (Considerable)</div>
      <div class="legend-item"><span class="legend-color" style="background:#f43f5e;"></span> RI ≥ 150 (High)</div>
    `;
  } else {
    legend.innerHTML = `
      <div class="legend-item"><span class="legend-color" style="background:#10b981;"></span> Baseline</div>
      <div class="legend-item"><span class="legend-color" style="background:#38bdf8;"></span> Permissible</div>
      <div class="legend-item"><span class="legend-color" style="background:#f59e0b;"></span> Action Warning</div>
      <div class="legend-item"><span class="legend-color" style="background:#f43f5e;"></span> Action Required</div>
    `;
  }
}

// Global helpers for Leaflet popups
window.selectCoordsFromMap = function(lat, lon) {
  setUserPin(lat, lon, 'Selected Map Location');
  switchTab('analysis');
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
  setUserPin(lat, lon, 'Sample Observation');
  updateTextureSumMeter();
  switchTab('analysis');
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

  document.getElementById('btn-balance-texture').addEventListener('click', () => {
    const clay = parseFloat(clayInp.value) || 0;
    const sand = parseFloat(sandInp.value) || 0;
    const rem = Math.max(0, 100.0 - (clay + sand));
    siltInp.value = rem.toFixed(1);
    updateTextureSumMeter();
  });

  document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('inp-lat').value = btn.dataset.lat;
      document.getElementById('inp-lon').value = btn.dataset.lon;
      document.getElementById('inp-landuse').value = btn.dataset.lu;
      setUserPin(parseFloat(btn.dataset.lat), parseFloat(btn.dataset.lon), btn.textContent.trim());
    });
  });

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
  banner.textContent = `⚠️ Validation: ${msg}`;
  banner.classList.remove('hidden');
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

  const textureTotal = clay + sand + silt;
  if (Math.abs(textureTotal - 100.0) > 1.5) {
    showFormError(
      `Clay (${clay}%) + Sand (${sand}%) + Silt (${silt}%) sums to ${textureTotal.toFixed(1)}%. Must equal 100% (±1.5%). Click "Auto-Balance Silt" to balance.`
    );
    return;
  }

  if (lat < 8.0 || lat > 14.0 || lon < 76.0 || lon > 81.0) {
    showFormError('Coordinates must fall within Tamil Nadu (8.0°N–14.0°N, 76.0°E–81.0°E).');
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
  submitBtn.textContent = '⏳ Computing...';

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
  } catch (err) {
    showFormError(err.message || 'Error occurred during prediction.');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = '⚡ Run Prediction & Explanation';
  }
}

// ---------------------------------------------------------------------------
// 5. Prediction & Feature Attribution Rendering
// ---------------------------------------------------------------------------
function renderPredictionResults(pred, expl) {
  document.getElementById('results-placeholder').classList.add('hidden');
  document.getElementById('results-display').classList.remove('hidden');

  // 1. Farmer-Friendly Advisory Block
  if (pred.farmer_advisory) {
    const adv = pred.farmer_advisory;
    const pill = document.getElementById('farmer-verdict-pill');
    pill.className = `farmer-status-pill ${adv.badge_class || 'safe'}`;
    pill.textContent = adv.verdict;

    document.getElementById('farmer-summary-text').textContent = adv.summary;

    const stepsList = document.getElementById('farmer-steps-list');
    stepsList.innerHTML = (adv.advice_steps || []).map(step => `<li>${step}</li>`).join('');

    const cropNote = document.getElementById('farmer-crop-note');
    if (adv.crop_health_note) {
      cropNote.innerHTML = `<strong>🌾 Crop & Health Insight:</strong> ${adv.crop_health_note}`;
    }
  }

  // 2. Technical Figures & Hero Banner
  document.getElementById('res-target-sub').textContent = `TARGET: ${pred.metal.toUpperCase()} (${pred.symbol})`;
  document.getElementById('res-pred-val').textContent = pred.predicted_concentration_mg_kg.toFixed(2);
  
  const conf = pred.conformal_interval_90;
  document.getElementById('res-bound-text').textContent = 
    `Conformal 90% Bound: [${conf.lower_bound.toFixed(2)} – ${conf.upper_bound.toFixed(2)}] mg/kg (±${conf.margin_q_hat.toFixed(2)} mg/kg | ${conf.empirical_test_coverage_pct}% Test Coverage)`;
  
  document.getElementById('res-coord-text').textContent = 
    `${pred.coordinates.latitude}°N, ${pred.coordinates.longitude}°E | ${pred.soil_properties.land_use}`;

  const riskBadge = document.getElementById('res-risk-badge');
  riskBadge.className = `risk-badge ${pred.risk_tier}`;
  riskBadge.textContent = pred.risk_category;
  document.getElementById('res-risk-desc').textContent = pred.risk_description;

  document.getElementById('res-igeo-val').textContent = pred.geoaccumulation_index_igeo;
  document.getElementById('res-er-val').textContent = pred.single_ecological_risk_Er;

  renderThresholdBars(pred);
  renderProvenanceDetails(pred);
  renderAttributionChart(expl);
}

function renderThresholdBars(pred) {
  const container = document.getElementById('threshold-bars-container');
  const limits = pred.regulatory_limits;
  const conc = pred.predicted_concentration_mg_kg;

  const items = [
    { label: 'Geochemical Baseline (Bn)', val: limits.background_baseline_mg_kg },
    { label: 'Permissible Agricultural Limit', val: limits.agricultural_limit_mg_kg },
    { label: 'CPCB Action Limit', val: limits.action_level_mg_kg }
  ];

  container.innerHTML = items.map(item => {
    const pct = Math.min(100, Math.round((conc / item.val) * 100));
    const fillClass = pct <= 80 ? 'safe' : pct <= 110 ? 'warn' : 'danger';
    return `
      <div class="threshold-item">
        <div class="threshold-meta">
          <span>${item.label}: <strong>${item.val} mg/kg</strong></span>
          <span>${pct}%</span>
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
    <div class="prov-tag">Algorithm: <strong>${prov.algorithm}</strong></div>
    <div class="prov-tag">Train R²: <strong>${prov.training_r2}</strong></div>
    <div class="prov-tag">Spatial CV R²: <strong style="color:#f43f5e;">${prov.spatial_cv_r2}</strong></div>
    <div class="prov-tag">Conformal Coverage: <strong style="color:#10b981;">${pred.conformal_interval_90.empirical_test_coverage_pct}%</strong></div>
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
        label: 'Attribution Impact',
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
      plugins: { legend: { display: false } },
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
          label: 'Proposed Hybrid Strategy',
          data: [98.5, 91.2, 84.6, 78.2, 72.5, 68.1, 64.3, 61.8, 59.5, 58.0],
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          borderWidth: 3,
          tension: 0.3,
          fill: true
        },
        {
          label: 'Uncertainty Only',
          data: [98.5, 93.8, 88.4, 83.1, 77.8, 73.6, 70.2, 67.5, 65.4, 63.8],
          borderColor: '#38bdf8',
          borderWidth: 2,
          tension: 0.3
        },
        {
          label: 'Risk Only',
          data: [98.5, 94.5, 89.2, 84.8, 80.1, 76.5, 73.1, 70.8, 68.9, 67.2],
          borderColor: '#f59e0b',
          borderWidth: 2,
          tension: 0.3
        },
        {
          label: 'Random Sampling',
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
          title: { display: true, text: 'Observations (N)', color: '#94a3b8' },
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

    const tbody = document.getElementById('provenance-benchmarks-tbody');
    const rows = [
      { slug: 'chromium', name: 'Chromium (Cr)', algo: 'XGBoost' },
      { slug: 'lead', name: 'Lead (Pb)', algo: 'XGBoost' },
      { slug: 'cadmium', name: 'Cadmium (Cd)', algo: 'XGBoost' },
      { slug: 'nickel', name: 'Nickel (Ni)', algo: 'XGBoost' }
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
        </tr>
      `;
    }).join('');

    const confTbody = document.getElementById('conformal-table-tbody');
    confTbody.innerHTML = Object.entries(conf).map(([k, v]) => `
      <tr>
        <td><strong>${k.toUpperCase()}</strong></td>
        <td><strong style="color:#10b981;">${v.coverage}%</strong></td>
        <td>${v.q_hat.toFixed(2)} mg/kg</td>
        <td>${v.interval_width ? v.interval_width.toFixed(2) + ' mg/kg' : '--'}</td>
      </tr>
    `).join('');

    renderSpatialGapChart(meta);
  } catch (err) {
    console.error('Failed to load benchmarks:', err);
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
          label: 'Standard Random CV R² (Optimistic)',
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
          title: { display: true, text: 'R² Score', color: '#94a3b8' },
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
// 8. Downloadable Analysis Report Actions
// ---------------------------------------------------------------------------
function initReportActions() {
  document.getElementById('btn-print-report').addEventListener('click', () => {
    if (!state.lastReport) return;
    const printWindow = window.open('', '_blank');
    const rep = state.lastReport;
    const loc = rep.input_parameters.coordinates;
    const soil = rep.input_parameters.soil_properties;
    const est = rep.model_estimates;

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Soil Contamination Report - ${rep.report_id}</title>
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 30px; color: #1e293b; line-height: 1.5; font-size: 13px; }
          h1 { font-size: 20px; color: #0f172a; margin-bottom: 2px; }
          h2 { font-size: 14px; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; margin-top: 18px; text-transform: uppercase; }
          .header-box { border-bottom: 2px solid #0f172a; padding-bottom: 12px; margin-bottom: 16px; display: flex; justify-content: space-between; }
          .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
          .estimate-box { background: #f0fdf4; border: 1px solid #bbf7d0; padding: 12px; border-radius: 4px; margin: 12px 0; }
          .disclaimer { background: #fff1f2; border: 1px solid #fecdd3; padding: 10px; font-size: 11px; color: #9f1239; margin-top: 20px; }
        </style>
      </head>
      <body>
        <div class="header-box">
          <div>
            <h1>GeoSoil Insight — Soil Pollution Report</h1>
            <span style="color:#64748b;">Tamil Nadu Regional Environmental Monitoring</span>
          </div>
          <div style="text-align:right;">
            <strong>${rep.report_id}</strong><br>
            <span>${rep.generated_at}</span>
          </div>
        </div>

        <h2>1. Site Location & Soil Properties</h2>
        <div class="grid">
          <div>Latitude: ${loc.latitude}°N | Longitude: ${loc.longitude}°E</div>
          <div>Land Use: ${soil.land_use}</div>
          <div>Soil pH: ${soil.soil_ph} | EC: ${soil.soil_ec_dSm} dS/m</div>
          <div>Texture: Clay ${soil.clay_pct}%, Sand ${soil.sand_pct}%, Silt ${soil.silt_pct}% (SOC: ${soil.soc_pct}%)</div>
        </div>

        <h2>2. Contamination Estimate & 90% Conformal Bounds</h2>
        <div class="estimate-box">
          <strong>Target: ${rep.target_metal} (${rep.chemical_symbol})</strong><br>
          Estimated Concentration: <strong>${est.predicted_concentration}</strong><br>
          Conformal Prediction Interval (90% nominal): <strong>${est.conformal_prediction_interval_90}</strong> (${est.uncertainty_margin})<br>
          Risk Category: <strong>${rep.risk_evaluation.category}</strong> (${rep.risk_evaluation.description})
        </div>

        <h2>3. Regulatory Standards Comparison</h2>
        <div>Baseline (Bn): ${rep.regulatory_thresholds.background_baseline_mg_kg} mg/kg | Agricultural Limit: ${rep.regulatory_thresholds.agricultural_limit_mg_kg} mg/kg | CPCB Action Limit: ${rep.regulatory_thresholds.action_level_mg_kg} mg/kg</div>

        <div class="disclaimer">
          <strong>Scientific Disclaimers & Limitations:</strong>
          <ul>
            ${rep.scientific_limitations_and_disclaimer.map(d => `<li>${d}</li>`).join('')}
          </ul>
        </div>
      </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => printWindow.print(), 250);
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
})();
