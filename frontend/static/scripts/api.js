const Api = {
  lang() {
    return localStorage.getItem("gllms:lang") === "ar" ? "ar" : "en";
  },

  withLang(url) {
    return `${url}${url.includes("?") ? "&" : "?"}lang=${this.lang()}`;
  },

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
    return this.get(this.withLang("/api/scenarios"));
  },

  getScenario(id) {
    return this.get(this.withLang(`/api/scenarios/${encodeURIComponent(id)}`));
  },

  runScenario(id, body) {
    return this.post(`/api/run/${encodeURIComponent(id)}`, body || {});
  },
};
