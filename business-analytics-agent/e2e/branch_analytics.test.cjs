const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const { spawn } = require('node:child_process');
const path = require('node:path');

let server, browser, base;
before(async () => {
  server = spawn(process.env.PYTHON || 'python3', ['-u', '-m', 'portfolio_demo.server', '--port', '0'], {
    cwd: path.resolve(__dirname, '..'), stdio: ['ignore', 'pipe', 'pipe'],
  });
  base = await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('Server startup timed out')), 10000);
    server.on('error', reject);
    server.on('exit', code => { clearTimeout(timer); reject(new Error(`Server exited: ${code}`)); });
    server.stdout.on('data', chunk => {
      const match = chunk.toString().match(/http:\/\/127\.0\.0\.1:\d+\//);
      if (match) { clearTimeout(timer); resolve(match[0]); }
    });
  });
  browser = await chromium.launch({ headless: true, channel: process.env.PLAYWRIGHT_CHANNEL || undefined });
});
after(async () => { await browser?.close(); server?.kill('SIGINT'); });

test('browser selects a branch and preserves missing history', async () => {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  try {
    await page.goto(base);
    await page.waitForFunction(() => document.querySelector('#status').textContent === 'Showing local sample data');
    await page.selectOption('#branch', 'BRANCH003');
    await page.waitForFunction(() => document.querySelector('#growth').textContent === 'No baseline');
    assert.equal(await page.locator('#share').textContent(), '20.0%');
    assert.equal(await page.locator('#rows tr.selected').count(), 1);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  } finally { await page.close(); }
});

test('failed metrics clear stale values and retry recovers', async () => {
  const page = await browser.newPage();
  try {
    await page.goto(base);
    await page.waitForFunction(() => document.querySelector('#total').textContent === '100.0');
    await page.route('**/api/metrics?**', route => route.fulfill({status: 503, contentType:'application/json', body:'{"error":"Temporarily unavailable"}'}));
    await page.selectOption('#year', '2024');
    await page.locator('#retry').waitFor({ state:'visible' });
    assert.equal(await page.locator('#total').textContent(), '—');
    assert.equal(await page.locator('#rows tr').count(), 0);
    await page.unroute('**/api/metrics?**');
    await page.click('#retry');
    await page.waitForFunction(() => document.querySelector('#total').textContent === '100.0');
  } finally { await page.close(); }
});

test('empty dataset shows an explicit empty state', async () => {
  const page = await browser.newPage();
  try {
    await page.route('**/api/years', route => route.fulfill({status:200,contentType:'application/json',body:'{"years":[],"synthetic":true}'}));
    await page.goto(base);
    await page.waitForFunction(() => document.querySelector('#status').textContent === 'No sample years available');
    assert.equal(await page.locator('#year').isDisabled(), true);
    assert.equal(await page.locator('#rows tr').count(), 0);
  } finally { await page.close(); }
});
