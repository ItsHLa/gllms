import { chromium } from "playwright-core";

const browser = await chromium.launch({ channel: "chrome" });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errs = [];
page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));

// AR boot -> dashboard
await page.goto("http://localhost:8000/lab", { waitUntil: "networkidle" });
await page.evaluate(() => localStorage.setItem("gllms:lang", "ar"));
await page.reload({ waitUntil: "networkidle" });
await page.waitForSelector(".attack-card", { timeout: 15000 });
await page.waitForTimeout(500);
const dash = await page.evaluate(() => ({
  title: document.querySelector(".attack-card-title").textContent.trim().slice(0, 40),
  cat: document.querySelector(".attack-card-cat").textContent.trim(),
  accent: getComputedStyle(document.querySelector(".attack-card")).getPropertyValue("--card-accent").trim(),
  sevBadge: document.querySelector(".severity-badge").textContent.trim(),
}));
console.log("DASH ar:", JSON.stringify(dash));

// open scenario -> article rendered in Arabic (marked v-html)
await page.click(".attack-card");
await page.waitForTimeout(900);
const art = await page.evaluate(() => {
  const h1 = document.querySelector(".scenario-head h1");
  const artH = document.querySelector(".article h2, .article h1");
  return {
    headTitle: h1 ? h1.textContent.trim().slice(0, 45) : null,
    articleHead: artH ? artH.textContent.trim() : null,
    firstP: document.querySelector(".article p")?.textContent.trim().slice(0, 50) || null,
  };
});
console.log("ARTICLE ar:", JSON.stringify(art, null, 1));

// live toggle to EN without reload -> same scenario refetched in English
await page.click(".lang-switch");
await page.waitForTimeout(1000);
const en = await page.evaluate(() => ({
  dir: document.documentElement.dir,
  headTitle: document.querySelector(".scenario-head h1").textContent.trim().slice(0, 45),
  articleH1: document.querySelector(".article h1")?.textContent.trim().slice(0, 45) || null,
  modeNote: document.querySelector(".sysprompt-note")?.textContent.trim().slice(0, 60) || null,
}));
console.log("LIVE EN toggle:", JSON.stringify(en, null, 1));
console.log("pageerrors:", errs.length ? errs : "none");
await browser.close();
