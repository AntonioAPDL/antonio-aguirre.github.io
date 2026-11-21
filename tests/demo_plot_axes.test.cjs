'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const { makeDemoData } = require('./fixtures/demo_plot_data.cjs');
const root = path.resolve(__dirname, '..');
const colors = { text: '#222', grid: '#ddd', line: '#168', surface: '#fff' };

function loadScript(filename, names) {
  const calls = [];
  const source = fs.readFileSync(path.join(root, 'public/js', filename), 'utf8');
  const context = {
    window: {}, Date, console,
    document: { readyState: 'loading', addEventListener() {}, documentElement: {} },
    getComputedStyle: () => ({ getPropertyValue: () => '' }),
    Plotly: { react: (...args) => calls.push(args), purge: () => calls.push(['purged']) }
  };
  context.window.Plotly = context.Plotly;
  // Expose private functions only in the test VM; production scripts stay encapsulated.
  vm.runInNewContext(source.replace(/\}\)\(\);\s*$/, `globalThis.api = {${names.join(',')}};})();`), context);
  return { api: context.api, calls };
}

function renderFlow(scale, scenario, overrides = {}) {
  const { api, calls } = loadScript('sanlorenzo_flow.js', ['UsgsIvPlot', 'extractSeries']);
  const data = makeDemoData(scenario);
  const plot = {
    config: { mode: 'discharge', yLabel: 'Discharge', dailyAvgMinCoverage: 0.9, ...overrides },
    currentScale: scale,
    chartEl: {},
    resolveTimelineWindow: () => [new Date(data.init - 20 * 86400000), new Date(+data.init + 10 * 86400000)],
    updateAriaLabel() {}, setLoadedState() {}, setStatus() {}
  };
  api.UsgsIvPlot.prototype.renderPlot.call(plot, {
    points: api.extractSeries(data.usgs).points,
    siteName: 'Big Trees', units: 'cfs', lastObs: data.init, lastRefresh: data.init,
    forecastPayload: data.flow
  });
  return calls[0];
}

function assertAutomatic(axis) {
  assert.equal(axis.autorange, true);
  assert.equal(axis.range, undefined);
  assert.equal(axis.autorangeoptions?.clipmax, undefined);
  assert.equal(axis.autorangeoptions?.maxallowed, undefined);
}

function assertLayoutLabels(layout) {
  assert.equal(layout.legend.yanchor, 'bottom');
  for (const annotation of layout.annotations || []) {
    assert.equal(annotation.xanchor, 'right');
    assert.equal(annotation.yanchor, 'top');
    assert.equal(annotation.font.color, layout.font.color);
    assert.equal(annotation.bgcolor, layout.hoverlabel.bgcolor);
  }
}

for (const scale of ['log1p', 'linear']) {
  for (const scenario of ['extreme', 'observed-peak', 'constant', 'missing']) {
    test(`flow ${scale}: ${scenario} retains automatic range and all interval bounds`, () => {
      const [, traces, layout] = renderFlow(scale, scenario);
      assertAutomatic(layout.yaxis);
      assertLayoutLabels(layout);
      assert.equal(layout.yaxis.rangemode, scale === 'linear' ? 'tozero' : 'nonnegative');
      assert.ok(traces.some((trace) => trace.fill === 'tonexty'));
      for (const trace of traces) {
        assert.equal(trace.y.length, trace.customdata.length);
        trace.y.forEach((value, i) => {
          assert.ok(Number.isFinite(value));
          const expected = scale === 'log1p' ? Math.log1p(trace.customdata[i]) : trace.customdata[i];
          assert.equal(value, expected);
        });
      }
      const peak = Math.max(...traces.flatMap((trace) => trace.y));
      if (scenario === 'extreme' || scenario === 'observed-peak' || scenario === 'missing') {
        assert.ok(peak > (scale === 'linear' ? 30 : 10));
      }
    });
  }
}

test('optional transformed 2-10 bounds extend autorange rather than clipping values', () => {
  const [, , layout] = renderFlow('log1p', 'extreme', { yMinLog1p: 2, yMaxLog1p: 10 });
  assertAutomatic(layout.yaxis);
  assert.deepEqual(Array.from(layout.yaxis.autorangeoptions.include), [2, 10]);
});

test('shared raw-unit bounds are transformed only for the log view', () => {
  for (const scale of ['log1p', 'linear']) {
    const [, , layout] = renderFlow(scale, 'extreme', { yMin: 0, yMax: 30 });
    assertAutomatic(layout.yaxis);
    assert.deepEqual(Array.from(layout.yaxis.autorangeoptions.include), [0, scale === 'log1p' ? Math.log1p(30) : 30]);
  }
});

for (const scenario of ['extreme', 'constant', 'missing', 'quiet']) {
  test(`climate ${scenario}: observed and forecast bands share an uncapped automatic axis`, () => {
    const { api, calls } = loadScript('gefs_forecast_panel.js', ['renderPrecipChart', 'renderSoilChart']);
    const { init, gefs } = makeDemoData(scenario);
    api.renderPrecipChart({}, gefs, init, 20, colors, []);
    api.renderSoilChart({}, gefs, init, 20, colors, []);
    assert.equal(calls.length, 2);
    for (const [, traces, layout] of calls) {
      assertAutomatic(layout.yaxis);
      assertLayoutLabels(layout);
      assert.ok(traces.some((trace) => trace.fill === 'toself'));
      assert.equal(layout.yaxis.tickformat, '.4~g');
      assert.ok(traces.flatMap((trace) => trace.y).every(Number.isFinite));
    }
    assert.equal(calls[0][2].yaxis.rangemode, 'tozero');
    assert.equal(calls[1][2].yaxis.rangemode, 'normal');
    if (scenario === 'extreme') {
      assert.equal(Math.max(...calls[0][1].flatMap((trace) => trace.y)), 500);
      assert.ok(Math.max(...calls[1][1].flatMap((trace) => trace.y)) > 0.9);
      assert.equal(Math.min(...calls[1][1].flatMap((trace) => trace.y)), 0.01);
    }
  });
}

test('no usable climate data purges the old plot and produces warnings', () => {
  const { api, calls } = loadScript('gefs_forecast_panel.js', ['renderPrecipChart', 'renderSoilChart']);
  const warnings = [];
  api.renderPrecipChart({}, {}, new Date(), 20, colors, warnings);
  api.renderSoilChart({}, {}, new Date(), 20, colors, warnings);
  assert.equal(calls.length, 2);
  assert.ok(calls.every((call) => call[0] === 'purged'));
  assert.equal(warnings.length, 2);
});

test('production page has no hard or reference range and keeps log1p as default', () => {
  const html = fs.readFileSync(path.join(root, 'demos.html'), 'utf8');
  assert.doesNotMatch(html, /data-y-(?:min|max)[\w-]*=/);
  assert.match(html, /data-discharge-scale="log1p"/);
});
