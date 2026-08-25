import { chromium } from "playwright-core";

const browser = await chromium.launch({ channel: "chrome" });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errs = [];
page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));

// EN boot -> straight into scenario, no dashboard
await page.goto("http://localhost:8000/lab", { waitUntil: "networkidle" });
await page.evaluate(() => localStorage.clear());
await page.reload({ waitUntil: "networkidle" });
await page.waitForSelector(".scenario-head h1", { timeout: 15000 });
await page.waitForTimeout(500);
const enBoot = await page.evaluate(() => ({
  title: document.querySelector(".scenario-head h1").textContent.trim().slice(0, 45),
  sidebarItems: document.querySelectorAll(".scenario-link").length,
  activeSidebar: document.querySelector(".scenario-link.active .scenario-link-title")?.textContent.trim().slice(0, 40) || null,
  dashboardGone: !document.querySelector(".dashboard, .attack-grid, .stats-row"),
  backBtnGone: !document.querySelector(".btn-back"),
  savedScenario: localStorage.getItem("gllms:scenario"),
}));

// switch scenario via sidebar
await page.click(".scenario-link:nth-child(1) li:nth-child(3) .scenario-link, .sidebar li:nth-child(3) .scenario-link");
await page.waitForTimeout(700);
const switched = await page.evaluate(() => ({
  title: document.querySelector(".scenario-head h1").textContent.trim().slice(0, 45),
}));

// AR toggle live: sidebar titles + head translate without reload
await page.click(".lang-switch");
await page.waitForTimeout(1000);
const arLive = await page.evaluate(() => ({
  dir: document.documentElement.dir,
  headTitle: document.querySelector(".scenario-head h1").textContent.trim().slice(0, 45),
  firstSidebarItem: document.querySelector(".scenario-link .scenario-link-title")?.textContent.trim().slice(0, 40),
  langBtn: document.querySelector(".lang-switch").textContent.trim(),
}));

console.log("EN boot:", JSON.stringify(enBoot, null, 1));
console.log("switched:", JSON.stringify(switched));
console.log("AR live:", JSON.stringify(arLive, null, 1));
console.log("pageerrors:", errs.length ? errs : "none");
await browser.close();
