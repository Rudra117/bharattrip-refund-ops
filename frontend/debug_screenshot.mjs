import puppeteer from 'puppeteer-core';
import path from 'path';

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ARTIFACTS_DIR = "C:\\Users\\Rudra Panchal\\.gemini\\antigravity\\brain\\0d6d988e-63e9-4cc1-9101-b3a62cca0d13";
const BASE_URL = "http://127.0.0.1:8008";

async function main() {
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: "new",
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR STACK:', err.stack || err.message));
  page.on('requestfailed', req => console.log('REQ FAILED:', req.url(), req.failure()?.errorText));

  await page.setViewport({ width: 1440, height: 900 });
  console.log("Navigating to", BASE_URL);
  await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });
  
  // Wait 3 seconds
  await new Promise(r => setTimeout(r, 3000));
  
  const content = await page.content();
  console.log("HTML snippet:", content.substring(content.indexOf('<body'), content.indexOf('<body') + 500));
  
  const heroEl = await page.$('#hero');
  console.log("Hero found:", !!heroEl);

  if (heroEl) {
    await heroEl.screenshot({ path: path.join(ARTIFACTS_DIR, 'screenshot_desktop_hero.png') });
    console.log("Captured hero!");
  }

  await browser.close();
}

main().catch(console.error);
