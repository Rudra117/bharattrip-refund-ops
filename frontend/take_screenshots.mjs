import puppeteer from 'puppeteer-core';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ARTIFACTS_DIR = "C:\\Users\\Rudra Panchal\\.gemini\\antigravity\\brain\\0d6d988e-63e9-4cc1-9101-b3a62cca0d13";
const BASE_URL = "http://127.0.0.1:8008";

async function main() {
  console.log("Launching Chrome via puppeteer-core...");
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: "new",
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();

  // 1. Desktop Screenshots (1440 x 900)
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 2 });
  console.log("Loading page at desktop resolution...");
  await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle0', timeout: 30000 });
  await page.waitForSelector('#hero');
  // Extra pause for Recharts / animations to finish
  await new Promise((r) => setTimeout(r, 2000));

  const sections = [
    { id: '#hero', filename: 'screenshot_desktop_hero.png' },
    { id: '#leaks', filename: 'screenshot_desktop_leaks.png' },
    { id: '#escalations', filename: 'screenshot_desktop_escalations.png' },
    { id: '#queue', filename: 'screenshot_desktop_queue.png' },
    { id: '#intake', filename: 'screenshot_desktop_intake.png' },
  ];

  for (const sec of sections) {
    const el = await page.$(sec.id);
    if (el) {
      await el.scrollIntoView();
      if (sec.id === '#intake') {
        const btn = await page.$('#intake button[type="submit"]');
        if (btn) {
          await btn.click();
          await new Promise((r) => setTimeout(r, 1200));
        }
      }
      await new Promise((r) => setTimeout(r, 800));
      const outPath = path.join(ARTIFACTS_DIR, sec.filename);
      await el.screenshot({ path: outPath });
      console.log(`Saved ${sec.filename}`);
    } else {
      console.warn(`Could not find ${sec.id}`);
    }
  }

  // 2. Mobile Screenshots (375 x 812)
  console.log("Switching to mobile viewport (375x812)...");
  await page.setViewport({ width: 375, height: 812, deviceScaleFactor: 2, isMobile: true });
  await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle0', timeout: 30000 });
  await page.waitForSelector('#hero');
  await new Promise((r) => setTimeout(r, 2000));

  const mobileSections = [
    { id: '#hero', filename: 'screenshot_mobile_hero.png' },
    { id: '#leaks', filename: 'screenshot_mobile_leaks.png' },
    { id: '#escalations', filename: 'screenshot_mobile_escalations.png' },
    { id: '#queue', filename: 'screenshot_mobile_queue.png' },
    { id: '#intake', filename: 'screenshot_mobile_intake.png' },
  ];

  for (const sec of mobileSections) {
    const el = await page.$(sec.id);
    if (el) {
      await el.scrollIntoView();
      if (sec.id === '#intake') {
        const btn = await page.$('#intake button[type="submit"]');
        if (btn) {
          await btn.click();
          await new Promise((r) => setTimeout(r, 1200));
        }
      }
      await new Promise((r) => setTimeout(r, 800));
      const outPath = path.join(ARTIFACTS_DIR, sec.filename);
      await el.screenshot({ path: outPath });
      console.log(`Saved ${sec.filename}`);
    }
  }

  await browser.close();
  console.log("All screenshots captured successfully!");
}

main().catch((err) => {
  console.error("Error capturing screenshots:", err);
  process.exit(1);
});
