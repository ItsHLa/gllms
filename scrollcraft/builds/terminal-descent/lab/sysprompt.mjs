import { chromium } from "playwright-core";

const browser = await chromium.launch({ channel: "chrome" });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errs = [];
page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));

async function openTry(id) {
  await page.evaluate((sid) => localStorage.setItem("gllms:scenario", sid), id);
  await page.goto("http://localhost:8000/lab", { waitUntil: "networkidle" });
  await page.waitForSelector("#tab-try:not([disabled])", { timeout: 15000 });
  await page.click("#tab-try");
  await page.waitForSelector(".sysprompt-content", { timeout: 10000 });
}

await page.goto("http://localhost:8000/lab", { waitUntil: "domcontentloaded" });
await page.evaluate(() => {
  localStorage.setItem("gllms:lang", "en");
  localStorage.setItem("gllms:scenario", "sql-injection-output");
});

// Scenario A: SQL injection
await openTry("sql-injection-output");
const sqlProtected = await page.evaluate(() =>
  document.querySelector(".sysprompt-content").textContent.trim().slice(0, 70)
);

// Scenario B: direct injection leak
await openTry("direct-prompt-injection-leak");
const leakProtected = await page.evaluate(() =>
  document.querySelector(".sysprompt-content").textContent.trim().slice(0, 70)
);

// Mode switch within scenario B -> prompt changes
await page.selectOption(".mode-select select", "vulnerable");
await page.waitForTimeout(300);
const leakVulnMode = await page.evaluate(() => document.querySelector(".mode-select select").value);
const leakVuln = await page.evaluate(() =>
  document.querySelector(".sysprompt-content").textContent.trim().slice(0, 70)
);

console.log("SQL protected  :", JSON.stringify(sqlProtected));
console.log("LEAK protected :", JSON.stringify(leakProtected));
console.log("LEAK mode:", leakVuln, "->", JSON.stringify(leakVuln));
console.log("all distinct:", sqlProtected !== leakProtected && leakProtected !== leakVuln);
console.log("pageerrors:", errs.length ? errs : "none");
await browser.close();
