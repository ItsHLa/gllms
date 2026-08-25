import { chromium } from "playwright-core";

const browser = await chromium.launch({ channel: "chrome" });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errs = [];
page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));

await page.goto("http://localhost:8000/lab", { waitUntil: "networkidle" });
await page.waitForSelector(".scenario-head h1", { timeout: 15000 });
await page.waitForTimeout(500);

// switch to vulnerable mode to see the warning note
await page.selectOption(".mode-select select", "vulnerable").catch(() => {});
await page.waitForTimeout(400);

const check = await page.evaluate(() => {
  const emojiRe = /[\u2300-\u27BF\u2B00-\u2BFF\u{1F000}-\u{1FAFF}\uFE0F]/gu;
  const bodyText = document.body.innerText;
  return {
    emojisInUI: (bodyText.match(emojiRe) || []).length,
    svgIcons: document.querySelectorAll("svg.icon").length,
    tabIconsSvg: document.querySelectorAll(".tab-icon svg.icon").length,
    syspromptIconSvg: !!document.querySelector(".sysprompt-icon svg.icon"),
    runBtnHasSvg: !!document.querySelector(".btn-run .icon"),
    runLabel: document.querySelector(".btn-run span")?.textContent.trim(),
    noteIcon: document.querySelector(".sysprompt-note .icon") ? "svg" : null,
    noteText: document.querySelector(".sysprompt-note span")?.textContent.trim().slice(0, 45) || null,
  };
});
console.log(JSON.stringify(check, null, 1));

// AR sanity after string edits
await page.click(".lang-switch");
await page.waitForTimeout(800);
const ar = await page.evaluate(() => ({
  dir: document.documentElement.dir,
  runLabel: document.querySelector(".btn-run span")?.textContent.trim(),
  noteText: document.querySelector(".sysprompt-note span")?.textContent.trim().slice(0, 40) || null,
}));
console.log("AR:", JSON.stringify(ar));
console.log("pageerrors:", errs.length ? errs : "none");
await browser.close();
