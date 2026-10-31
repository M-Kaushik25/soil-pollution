/**
 * GeoSoil Insight — Centralized API Client Module
 * Provides standardized HTTP communication with the FastAPI backend.
 * Never returns fake fallback data; surfaces genuine API errors.
 */

(function() {
  'use strict';

  const API_BASE = window.location.origin.includes(":8000") 
    ? window.location.origin 
    : "http://127.0.0.1:8000";

async function fetchJson(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        "Accept": "application/json",
        "Content-Type": "application/json",
        ...(options.headers || {})
      }
    });

    if (!res.ok) {
      let errorDetail = `HTTP ${res.status}: ${res.statusText}`;
      try {
        const errorBody = await res.json();
        if (errorBody && errorBody.detail) {
          if (Array.isArray(errorBody.detail)) {
            errorDetail = errorBody.detail.map(d => `${d.loc ? d.loc.join('.') + ': ' : ''}${d.msg}`).join("; ");
          } else {
            errorDetail = errorBody.detail;
          }
        }
      } catch (_) {}
      throw new Error(errorDetail);
    }

    return await res.json();
  } catch (err) {
    console.error(`API Error on [${options.method || 'GET'}] ${endpoint}:`, err);
    throw err;
  }
}

const api = {
  getBaseUrl() {
    return API_BASE;
  },

  async checkHealth() {
    return fetchJson("/health");
  },

  async getManifest() {
    return fetchJson("/manifest");
  },

  async getMetals() {
    return fetchJson("/metals");
  },

  async getInSituSamples(limit = 450) {
    return fetchJson(`/samples?limit=${limit}`);
  },

  async getPollutionMap(maxPoints = 400) {
    return fetchJson(`/pollution-map?max_points=${maxPoints}`);
  },

  async predictSoil(payload, metal = "chromium") {
    return fetchJson(`/predict?metal=${encodeURIComponent(metal)}`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  async getExplanation(payload, metal = "chromium") {
    return fetchJson(`/explanation?metal=${encodeURIComponent(metal)}`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  async getSamplingPriority(payload) {
    return fetchJson("/sampling-priority", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  async getSamplingRecommendations(topK = 15) {
    return fetchJson(`/sampling-recommendations?top_k=${topK}`);
  },

  async getModelPerformance() {
    return fetchJson("/model-performance");
  },

  async generateReport(payload, metal = "chromium", notes = "") {
    return fetchJson("/report/generate", {
      method: "POST",
      body: JSON.stringify({
        location_input: payload,
        metal: metal,
        notes: notes
      })
    });
  }
};

  // Global export for script-tag loading (avoids file:// CORS module blockage)
  if (typeof window !== "undefined") {
    window.api = api;
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { api };
  }
})();

