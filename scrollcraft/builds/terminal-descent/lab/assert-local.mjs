#!/usr/bin/env node
// Build-local variant of the skill's worldflight-assert.mjs for a poster-world
// flight (no clips exist, so the clip-lerp / deadband / painted-frame checks do
// not apply). Everything else is kept faithful: geometry, flow rule, seam band,
// copy transform cap, leg opacity, console errors, reduced-motion contract.
// Adds checks for this build's bespoke systems: per-leg layer motion, chat
// phase machine, depth readout, verify-state publication.
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
const { chromium } = createRequire(path.join(process.cwd(), "package.json"))("playwright-core");

const argv = process.argv.slice(2);
const arg = (n, d) => { const i = argv.indexOf(n); return i > -1 && argv[i + 1] ? argv[i + 1] : d; };
const URL = arg("--url", "http://localhost:4520");

const CHROME = [
  process.env.SCROLLCRAFT_CHROME,
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
].find((p) => p && fs.existsSync(p));

let pass = 0, fail = 0;
const ok = (name, cond, note = "") => {
  if (cond) { pass++; console.log(`  PASS  ${name}${note ? "  " + note : ""}`); }
  else { fail++; console.log(`  FAIL  ${name}${note ? "  " + note : ""}`); }
};

const browser = await chromium.launch({ executablePath: CHROME, headless: true });

{
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const errs = [];
  page.on("console", (m) => { if (m.type() === "error") errs.push(m.text()); });
  page.on("pageerror", (e) => errs.push(String(e)));
  await page.goto(URL, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("html.sc-ready", { timeout: 15000 });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(900);

  const geom = await page.evaluate(() => {
    const segs = [...document.querySelectorAll("[data-sc-segment]")];
    const total = segs.reduce((s, el) => s + (parseFloat(el.dataset.scW) || 1.3), 0);
    const spacer = document.querySelector("[data-sc-spacer]");
    const stage = document.querySelector("[data-sc-world]");
    return {
      vh: innerHeight,
      weights: segs.map((el) => parseFloat(el.dataset.scW) || 1.3),
      spacerH: spacer.getBoundingClientRect().height,
      wantH: Math.round((total + 1) * innerHeight),
      docH: document.body.scrollHeight,
      stagePos: getComputedStyle(stage).position,
    };
  });
  console.log(`\nDESKTOP  vh=${geom.vh}  weights=[${geom.weights}]`);

  ok("spacer height = (sum weights + 1) x vh",
    Math.abs(geom.spacerH - geom.wantH) <= 1, `got ${Math.round(geom.spacerH)}px want ${geom.wantH}px`);
  ok("stage is position:fixed", geom.stagePos === "fixed");

  const flow = await page.evaluate(() => {
    const bad = [];
    document.querySelectorAll("body *").forEach((el) => {
      const cs = getComputedStyle(el);
      if (cs.position === "fixed" || cs.position === "absolute") return;
      if (el.hasAttribute("data-sc-spacer") || el.hasAttribute("data-sc-mode")) return;
      const r = el.getBoundingClientRect();
      if (r.height > 4 && r.bottom > innerHeight + 4) {
        bad.push(el.tagName + "." + (el.className || "").toString().slice(0, 30));
      }
    });
    return bad;
  });
  ok("nothing in document flow but the spacer", flow.length === 0, flow.join(", "));

  // ---- seam band -----------------------------------------------------------
  const seg0 = geom.weights[0];
  const boundary = seg0 * geom.vh;
  const seamW = await page.evaluate(() =>
    parseFloat(document.querySelector("[data-sc-mode]").getAttribute("data-sc-seam")) || 0.16);
  const half = (seamW / 2) * geom.vh;
  const band = [];
  for (let i = 0; i < 5; i++) {
    const y = Math.round(boundary - half + (2 * half) * (i / 4)) + (i === 4 ? 3 : 0);
    await page.evaluate((y) => scrollTo({ top: y, behavior: "instant" }), y);
    await page.waitForTimeout(120);
    band.push(await page.evaluate(() =>
      [...document.querySelectorAll("[data-sc-segment]")].map((s) =>
        +(parseFloat(getComputedStyle(s).opacity) || 0).toFixed(4))));
  }
  const incoming = band.map((b) => b[1]);
  const outgoing = band.map((b) => b[0]);
  console.log(`  seam band  incoming=[${incoming}]  outgoing=[${outgoing}]`);
  ok("incoming leg opacity is strictly monotone across the seam",
    incoming.every((v, i) => i === 0 || v > incoming[i - 1]));
  ok("incoming leg starts at 0 and ends at 1", incoming[0] <= 0.02 && incoming[4] >= 0.98);
  ok("outgoing leg holds full opacity while the incoming one is still arriving",
    incoming.every((v, i) => v >= 0.999 || outgoing[i] >= 0.999), `[${outgoing}]`);
  ok("outgoing leg only releases once it is fully covered",
    outgoing[4] === 0 && incoming[4] >= 0.999);

  // ---- copy transform cap --------------------------------------------------
  const maxT = [];
  for (let i = 0; i <= 12; i++) {
    const y = Math.round((geom.docH - geom.vh) * (i / 12));
    await page.evaluate((y) => scrollTo({ top: y, behavior: "instant" }), y);
    await page.waitForTimeout(60);
    maxT.push(await page.evaluate(() => {
      let m = 0;
      document.querySelectorAll("[data-sc-copy]").forEach((el) => {
        const t = new DOMMatrixReadOnly(getComputedStyle(el).transform);
        m = Math.max(m, Math.abs(t.m42), Math.abs(t.m41));
      });
      return +m.toFixed(2);
    }));
  }
  const worstT = Math.max(...maxT);
  ok("copy never translates past 4vh", worstT <= geom.vh * 0.04 + 1,
    `worst ${worstT}px, cap ${(geom.vh * 0.04).toFixed(0)}px`);

  // ---- every leg reaches full opacity --------------------------------------
  const reach = {};
  for (let i = 0; i <= 24; i++) {
    const y = Math.round((geom.docH - geom.vh) * (i / 24));
    await page.evaluate((y) => scrollTo({ top: y, behavior: "instant" }), y);
    await page.waitForTimeout(260);
    const s = await page.evaluate(() =>
      [...document.querySelectorAll("[data-sc-segment]")].map((el) =>
        parseFloat(getComputedStyle(el).opacity) || 0));
    s.forEach((op, li) => { reach[li] = Math.max(reach[li] || 0, op); });
  }
  ok("every leg reaches full opacity",
    Object.values(reach).every((op) => op >= 0.99),
    Object.entries(reach).map(([i, op]) => `${i}:${op.toFixed(2)}`).join(" "));

  // ---- bespoke layer motion: --sp advances and moves real layers -----------
  const yA = Math.round(0.12 * seg0 * geom.vh);
  const yB = Math.round(0.85 * seg0 * geom.vh);
  await page.evaluate((y) => scrollTo({ top: y, behavior: "instant" }), yA);
  await page.waitForTimeout(300);
  const a = await page.evaluate(() => ({
    sp: parseFloat(getComputedStyle(document.querySelectorAll("[data-sc-segment]")[0]).getPropertyValue("--sp")),
    tf: getComputedStyle(document.querySelector(".seg--hall .l-near")).transform,
    chat: document.querySelector(".chat").dataset.phase,
    depth: document.getElementById("depthVal").textContent,
    vs: document.querySelector("[data-sc-world]").getAttribute("data-sc-verify-state"),
  }));
  await page.evaluate((y) => scrollTo({ top: y, behavior: "instant" }), yB);
  await page.waitForTimeout(400);
  const b = await page.evaluate(() => ({
    sp: parseFloat(getComputedStyle(document.querySelectorAll("[data-sc-segment]")[0]).getPropertyValue("--sp")),
    tf: getComputedStyle(document.querySelector(".seg--hall .l-near")).transform,
    chat: document.querySelector(".chat").dataset.phase,
  }));
  ok("per-leg progress var advances inside a leg", b.sp > a.sp + 0.3, `${a.sp} -> ${b.sp}`);
  ok("scene layers move with leg progress", a.tf !== b.tf);
  ok("chat wakes before leg 2", b.chat !== "idle", `phase=${b.chat}`);
  ok("depth readout ticks off the track", /^−0\d{3}m$/.test(a.depth), a.depth);
  ok("verify-state publishes rendered values", /^\d+:\d+:\d+:/.test(a.vs || ""), a.vs);

  await page.evaluate((y) => scrollTo({ top: y, behavior: "instant" }), Math.round(6.2 * geom.vh));
  await page.waitForTimeout(400);
  const peakPhase = await page.evaluate(() => document.querySelector(".chat").dataset.phase);
  ok("chat reaches hijack inside the peak leg", peakPhase === "hijack" || peakPhase === "guard", `phase=${peakPhase}`);

  await page.evaluate((y) => scrollTo({ top: y, behavior: "instant" }), geom.docH);
  await page.waitForTimeout(500);
  const endState = await page.evaluate(() => ({
    phase: document.querySelector(".chat").dataset.phase,
    finaleOp: parseFloat(getComputedStyle(document.querySelector(".sc-copy--finale")).opacity),
  }));
  ok("chat resolves to the run prompt at the end", endState.phase === "prompt");
  ok("finale copy holds at full opacity on the last screen", endState.finaleOp >= 0.99, `opacity ${endState.finaleOp}`);

  ok("no console errors", errs.length === 0, errs.slice(0, 3).join(" | "));
  await page.close();
}

{
  const page = await browser.newPage({
    viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1, reducedMotion: "reduce",
  });
  await page.goto(URL, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("html.sc-ready", { timeout: 15000 });
  await page.waitForTimeout(800);
  console.log("\nREDUCED MOTION");

  const rmSeen = { legs: {}, copy: {} };
  for (let i = 0; i <= 20; i++) {
    const h = await page.evaluate(() => document.body.scrollHeight - innerHeight);
    await page.evaluate((y) => scrollTo({ top: y, behavior: "instant" }), Math.round(h * (i / 20)));
    await page.waitForTimeout(90);
    const s = await page.evaluate(() => ({
      legs: [...document.querySelectorAll("[data-sc-segment]")].map((el) => ({
        op: parseFloat(getComputedStyle(el).opacity) || 0,
      })),
      copy: [...document.querySelectorAll("[data-sc-copy]")].map((el) => ({
        t: (el.textContent || "").trim().replace(/\s+/g, " ").slice(0, 24),
        op: parseFloat(getComputedStyle(el).opacity) || 0,
        tf: getComputedStyle(el).transform,
      })),
      layers: [...document.querySelectorAll("[data-sc-segment] .layer")].map((el) => getComputedStyle(el).transform).slice(0, 3),
    }));
    s.legs.forEach((l, k) => { rmSeen.legs[k] = rmSeen.legs[k] || { op: 0 }; rmSeen.legs[k].op = Math.max(rmSeen.legs[k].op, l.op); });
    s.copy.forEach((c) => {
      rmSeen.copy[c.t] = rmSeen.copy[c.t] || { op: 0, tf: new Set() };
      rmSeen.copy[c.t].op = Math.max(rmSeen.copy[c.t].op, c.op);
      rmSeen.copy[c.t].tf.add(c.tf);
    });
    if (i === 10) rmSeen.midLayers = s.layers;
  }
  await page.waitForTimeout(500);

  ok("every leg's scene still reaches full opacity",
    Object.values(rmSeen.legs).every((l) => l.op >= 0.99),
    Object.entries(rmSeen.legs).map(([i, l]) => `${i}:${l.op.toFixed(2)}`).join(" "));
  ok("no copy transform",
    Object.values(rmSeen.copy).every((c) => [...c.tf].every((t) => t === "none")));
  ok("every copy block still reaches full opacity",
    Object.values(rmSeen.copy).every((c) => c.op >= 0.99),
    Object.entries(rmSeen.copy).map(([t, c]) => `${c.op.toFixed(2)} "${t}"`).join(" | "));
  await page.close();
}

await browser.close();
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
