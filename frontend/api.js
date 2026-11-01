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

  async getDashboardSummary() {
    return fetchJson("/dashboard/summary");
  },

  async getManifest() {
    return fetchJson("/manifest");
  },

  async getMetals() {
    return fetchJson("/metals");
  },

  async getMetalStatistics(metal) {
    return fetchJson(`/metals/${encodeURIComponent(metal)}/statistics`);
  },

  async getIndustrialAreas() {
    return fetchJson("/industrial-areas");
  },

  async getAnalyticsSummary(params = {}) {
    const q = new URLSearchParams();
    if (params.district) q.append("district", params.district);
    if (params.industrial_area) q.append("industrial_area", params.industrial_area);
    if (params.metal) q.append("metal", params.metal);
    return fetchJson(`/analytics/summary?${q.toString()}`);
  },

  async getInSituSamples(params = 500) {
    if (typeof params === "number") {
      return fetchJson(`/samples?limit=${params}`);
    }
    const q = new URLSearchParams();
    if (params.limit) q.append("limit", params.limit);
    if (params.offset) q.append("offset", params.offset);
    if (params.district) q.append("district", params.district);
    if (params.industrial_area) q.append("industrial_area", params.industrial_area);
    if (params.metal) q.append("metal", params.metal);
    if (params.source) q.append("source", params.source);
    if (params.sample_matrix) q.append("sample_matrix", params.sample_matrix);
    if (params.qc_status) q.append("qc_status", params.qc_status);
    if (params.search) q.append("search", params.search);
    if (params.sort_by) q.append("sort_by", params.sort_by);
    if (params.sort_order) q.append("sort_order", params.sort_order);
    return fetchJson(`/samples?${q.toString()}`);
  },

  async getSampleById(sampleId) {
    return fetchJson(`/samples/${encodeURIComponent(sampleId)}`);
  },

  async getPollutionMap(params = {}) {
    const q = new URLSearchParams();
    if (typeof params === "number") {
      q.append("max_points", params);
    } else {
      if (params.maxPoints) q.append("max_points", params.maxPoints);
      if (params.district) q.append("district", params.district);
      if (params.industrial_area) q.append("industrial_area", params.industrial_area);
      if (params.metal) q.append("metal", params.metal);
    }
    return fetchJson(`/pollution-map?${q.toString()}`);
  },

  async getSoilHealth(params = {}) {
    const q = new URLSearchParams();
    if (params.district) q.append("district", params.district);
    if (params.industrial_area) q.append("industrial_area", params.industrial_area);
    if (params.sample_id) q.append("sample_id", params.sample_id);
    if (params.limit) q.append("limit", params.limit);
    if (params.offset) q.append("offset", params.offset);
    return fetchJson(`/soil-health?${q.toString()}`);
  },

  async assessRisk(payload) {
    return fetchJson("/assessment", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  async getDataSources() {
    return fetchJson("/data-sources");
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

