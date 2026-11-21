'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const { makeDemoData } = require('../fixtures/demo_plot_data.cjs');

const baseUrl = process.env.DEMO_BASE_URL || 'http://127.0.0.1:4012';
const output = process.env.DEMO_QA_DIR || fs.mkdtempSync(path.join(os.tmpdir(), 'demo-axis-qa-'));
const selectors = ['.usgs-iv-plot__chart', '.gefs-forecast-precip', '.gefs-forecast-soil'];
const results = [];
fs.mkdirSync(output, { recursive: true });

async function checkBounds(page, label) {
  const plots = await page.evaluate((selectors) => selectors.map((selector) => {
    const plot = document.querySelector(selector);
    const axis = plot._fullLayout.yaxis;
    const values = plot.data
      .filter((trace) => trace.visible !== false && trace.visible !== 'legendonly')
      .flatMap((trace) => Array.from(trace.y || []).filter(Number.isFinite));
    const rect = plot.getBoundingClientRect();
    const legend = plot.querySelector('.legend')?.getBoundingClientRect();
    return {
      selector, range: axis.range, autorange: axis.autorange,
      min: Math.min(...values), max: Math.max(...values),
      ticks: Array.from(plot.querySelectorAll('.ytick text')).map((node) => node.textContent),
      legendBottom: legend?.bottom,
      plotTop: rect.top + plot._fullLayout._size.t,
      labelsWithinChart: Array.from(plot.querySelectorAll('.annotation-text')).every((node) => {
        const label = node.getBoundingClientRect();
        return label.left >= rect.left && label.right <= rect.right;
      })
    };
  }), selectors);
  for (const plot of plots) {
    assert.equal(plot.autorange, true, `${label}: ${plot.selector} must remain automatic`);
    assert.ok(Number.isFinite(plot.min) && Number.isFinite(plot.max), `${label}: missing values`);
    assert.ok(plot.range[1] > plot.range[0], `${label}: degenerate range`);
    assert.ok(plot.range[0] <= plot.min + 1e-10, `${label}: lower values clipped ${JSON.stringify(plot)}`);
    assert.ok(plot.range[1] >= plot.max - 1e-10, `${label}: upper values clipped ${JSON.stringify(plot)}`);
    assert.ok(plot.range[1] > plot.max, `${label}: missing headroom`);
    assert.equal(new Set(plot.ticks).size, plot.ticks.length, `${label}: duplicate tick labels`);
    assert.ok(plot.legendBottom <= plot.plotTop, `${label}: legend overlaps the plotting area`);
    assert.ok(plot.labelsWithinChart, `${label}: annotation clipped by chart edge`);
  }
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false,
    `${label}: page-wide overflow`);
  results.push({ label, plots });
  return plots;
}

async function main() {
  const browser = await chromium.launch({
    ...(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {}),
    headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage']
  });
  try {
    for (const scenario of ['extreme', 'observed-peak', 'constant', 'missing', 'quiet']) {
      for (const width of [1440, 390]) {
        for (const theme of ['light', 'dark']) {
          const context = await browser.newContext({ viewport: { width, height: 1000 } });
          const page = await context.newPage();
          const errors = [];
          page.on('pageerror', (error) => errors.push(error.message));
          const data = makeDemoData(scenario);
          await page.addInitScript((theme) => localStorage.setItem('theme', theme), theme);
          await page.route('https://waterservices.usgs.gov/**', (route) =>
            route.fulfill({ json: data.usgs }));
          await page.route('**/big_trees_latest.json*', (route) => route.fulfill({ json: data.flow }));
          await page.route('**/gefs_big_trees_latest.json*', (route) => route.fulfill({ json: data.gefs }));
          await page.route('**/climate_daily_ppt_soil.csv*', (route) => route.fulfill({
            contentType: 'text/csv',
            body: 'timestamp,daily_avg_ppt,daily_avg_soil_ERA5,daily_avg_soil_NWM_SOIL_M,daily_avg_soil_NWM_SOIL_W\n'
          }));
          // Keep CSS and application scripts from the build under test, not production.
          await page.route('https://antonio-de-leon.com/public/**', async (route) => {
            const url = new URL(route.request().url());
            const response = await page.request.get(`${baseUrl}${url.pathname}`);
            return route.fulfill({ response });
          });
          await page.goto(`${baseUrl}/demos/`, { waitUntil: 'networkidle' });
          await page.waitForFunction((selectors) => selectors.every((selector) => {
            const plot = document.querySelector(selector);
            return plot && plot._fullLayout && plot.data?.length;
          }), selectors);
          const label = `${scenario}-${width}-${theme}`;
          const initial = await checkBounds(page, `${label}-log1p`);
          assert.equal(await page.locator('[data-plot-scale="log1p"]').getAttribute('aria-pressed'), 'true');
          assert.ok(initial[0].range[0] >= 0);

          await page.locator('[data-plot-scale="linear"]').click();
          await page.waitForFunction(() => document.querySelector('.usgs-iv-plot__chart')._fullLayout.yaxis.rangemode === 'tozero');
          const linear = await checkBounds(page, `${label}-linear`);
          assert.equal(linear[0].range[0], 0);
          assert.equal(linear[1].range[0], 0);

          // Hiding a complete forecast group must refit; restoring it must restore the upper band.
          await page.evaluate(async () => {
            const plot = document.querySelector('.usgs-iv-plot__chart');
            const indices = plot.data.flatMap((trace, index) => trace.legendgroup === 'NWS medium' ? [index] : []);
            await Plotly.restyle(plot, { visible: 'legendonly' }, indices);
          });
          await checkBounds(page, `${label}-hidden-forecast`);
          if (scenario === 'extreme') {
            const max = await page.evaluate(() => document.querySelector('.usgs-iv-plot__chart')._fullLayout.yaxis.range[1]);
            assert.ok(max < linear[0].range[1], 'hiding a high band must reduce the range');
          }
          await page.evaluate(async () => {
            const plot = document.querySelector('.usgs-iv-plot__chart');
            await Plotly.restyle(plot, { visible: true });
          });
          await checkBounds(page, `${label}-restored-forecast`);
          await page.locator('[data-plot-scale="log1p"]').click();
          await page.waitForFunction(() => document.querySelector('.usgs-iv-plot__chart')._fullLayout.yaxis.rangemode === 'nonnegative');

          // Reapplying automatic ranges must recover from an intentionally cropped manual zoom.
          await page.evaluate(async (selectors) => {
            for (const selector of selectors) {
              const plot = document.querySelector(selector);
              await Plotly.relayout(plot, { 'yaxis.range': [0.1, 0.2] });
              await Plotly.relayout(plot, { 'yaxis.autorange': true });
            }
          }, selectors);
          await checkBounds(page, `${label}-reset`);
          if (scenario === 'quiet') {
            await page.evaluate(() => document.querySelector('[data-theme-toggle]').click());
            await page.waitForFunction((selectors) => selectors.every((selector) => {
              const plot = document.querySelector(selector);
              const text = getComputedStyle(document.documentElement).getPropertyValue('--text-color').trim();
              return plot._fullLayout.font.color === text && plot._fullLayout.shapes[0]?.line.color === text;
            }), selectors);
            await checkBounds(page, `${label}-theme-switch`);
            await page.evaluate(() => document.querySelector('[data-theme-toggle]').click());
            await page.waitForFunction((selectors) => selectors.every((selector) => {
              const plot = document.querySelector(selector);
              return plot._fullLayout.font.color === getComputedStyle(document.documentElement).getPropertyValue('--text-color').trim();
            }), selectors);
          }
          if (scenario === 'extreme' || scenario === 'quiet') {
            for (const selector of selectors) {
              await page.locator(selector).screenshot({
                path: path.join(output, `${label}-${selector.slice(1)}.png`)
              });
            }
          }
          assert.deepEqual(errors, [], `${label}: browser exceptions`);
          await context.close();
        }
      }
    }

    // Confirm the reference-window escape hatch on the actual pinned Plotly release.
    const page = await browser.newPage();
    await page.goto(`${baseUrl}/demos/`, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => !!window.Plotly);
    const ranges = await page.evaluate(async () => {
      const plot = document.createElement('div');
      document.body.appendChild(plot);
      const axis = { autorange: true, rangemode: 'nonnegative', autorangeoptions: { include: [2, 10] } };
      await Plotly.newPlot(plot, [{ y: [3, 4, 5] }], { yaxis: axis });
      const reference = plot._fullLayout.yaxis.range.slice();
      await Plotly.react(plot, [{ y: [0, 5, 12] }], { yaxis: axis });
      return [reference, plot._fullLayout.yaxis.range.slice()];
    });
    assert.ok(ranges[0][0] <= 2 && ranges[0][1] >= 10);
    assert.ok(ranges[1][0] <= 0 && ranges[1][1] > 12);
    await page.close();
    fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify(results, null, 2));
    console.log(`PASS: ${results.length} browser checks; 5 scenarios, both scales, 2 widths, 2 themes. Evidence: ${output}`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
