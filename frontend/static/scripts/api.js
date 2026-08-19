const Api = {
  async get(url) {
    const res = await fetch(url);
    if (!res.ok) {
      const data = await res.json().catch(() => null);
      const detail = data?.detail;
      const msg = typeof detail === "object" ? JSON.stringify(detail, null, 2) : (detail || `Request failed (${res.status})`);
      throw new Error(msg);
    }
    return res.json();
  },

  async post(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => null);
      const detail = data?.detail;
      const msg = typeof detail === "object" ? JSON.stringify(detail, null, 2) : (detail || `Request failed (${res.status})`);
      throw new Error(msg);
    }
    return res.json();
  },

  listScenarios() {
    return this.get("/api/scenarios");
  },

  getScenario(id) {
    return this.get(`/api/scenarios/${encodeURIComponent(id)}`);
  },

  runScenario(id, code) {
    return this.post(`/api/run/${encodeURIComponent(id)}`, { code });
  },
};
