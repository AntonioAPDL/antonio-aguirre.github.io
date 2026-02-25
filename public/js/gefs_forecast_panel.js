(() => {
  'use strict';

  if (window.__gefsForecastPanelInitialized) return;
  window.__gefsForecastPanelInitialized = true;

  function parseDate(value) {
    if (!value) return null;
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  function formatDate(value) {
    const date = parseDate(value);
    if (!date) return '--';
    try {
      return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
    } catch (err) {
      return date.toISOString();
    }
  }

  function numberOrNull(value) {
    if (value === null || value === undefined) return null;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function seriesToXY(points) {
    if (!Array.isArray(points)) return { x: [], y: [] };
    const x = [];
    const y = [];
    points.forEach((point) => {
      if (!point || !point.t) return;
      const date = parseDate(point.t);
      const value = numberOrNull(point.v);
      if (!date || value === null) return;
      x.push(date);
      y.push(value);
    });
    return { x, y };
  }

  function buildBandTrace(low, high, name, color) {
    const lower = seriesToXY(low);
    const upper = seriesToXY(high);
    if (!lower.x.length || !upper.x.length) return null;
    return {
      x: lower.x.concat(upper.x.slice().reverse()),
      y: lower.y.concat(upper.y.slice().reverse()),
      type: 'scatter',
      fill: 'toself',
      fillcolor: color,
      line: { color: 'rgba(0,0,0,0)' },
      name,
      hoverinfo: 'skip',
      showlegend: true
    };
  }

  function buildLineTrace(points, name, color, dash) {
    const series = seriesToXY(points);
    return {
      x: series.x,
      y: series.y,
      type: 'scatter',
      mode: 'lines',
      name,
      line: { color, width: 2, dash: dash || 'solid' },
      showlegend: true
    };
  }

  function getThemeColors() {
    const styles = getComputedStyle(document.documentElement);
    return {
      text: styles.getPropertyValue('--text-color').trim() || '#1f2933',
      grid: styles.getPropertyValue('--border-color').trim() || '#e2e8f0',
      accent: styles.getPropertyValue('--accent-color').trim() || '#1b63c6'
    };
  }

  function layout(title, yTitle, colors) {
    return {
      margin: { l: 56, r: 18, t: 26, b: 48 },
      title: { text: title, font: { size: 14, color: colors.text } },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: { color: colors.text, family: 'Source Sans Pro, Helvetica, Arial, sans-serif' },
      xaxis: { type: 'date', title: 'Valid time', gridcolor: colors.grid },
      yaxis: { title: yTitle, gridcolor: colors.grid },
      legend: { orientation: 'h', y: 1.14, x: 0 }
    };
  }

  function levelSortKey(level) {
    const match = String(level).match(/^([0-9.]+)\s*-/);
    return match ? Number(match[1]) : 999;
  }

  function setStatus(el, payload, warning) {
    if (!el) return;
    const generated = payload ? formatDate(payload.generated_at_utc) : '--';
    const initTime = payload ? formatDate(payload.init_time_utc) : '--';
    const members = payload && Number.isFinite(Number(payload.member_count))
      ? Number(payload.member_count)
      : '--';
    const missing = payload && Array.isArray(payload.missing_levels) && payload.missing_levels.length
      ? `Missing layers: ${payload.missing_levels.join(', ')}`
      : 'All configured layers resolved';
    el.textContent = `Init: ${initTime} | Generated: ${generated} | Members: ${members} | ${missing}${warning ? ` | ${warning}` : ''}`;
    el.classList.toggle('plot-status--error', Boolean(warning));
  }

  function buildFetchUrl(baseUrl) {
    const url = new URL(baseUrl, window.location.origin);
    // Bust browser/proxy caches so periodic refresh checks latest artifact.
    url.searchParams.set('_ts', String(Date.now()));
    return url.toString();
  }

  function renderPanel(container, payload) {
    const precipEl = container.querySelector('.gefs-forecast-precip');
    const soilEl = container.querySelector('.gefs-forecast-soil');
    const statusEl = container.querySelector('.gefs-forecast-status');
    const colors = getThemeColors();

    const staleHours = numberOrNull(container.dataset.staleHours) ?? numberOrNull(payload.stale_after_hours) ?? 12;
    let staleWarning = '';
    const generatedDate = parseDate(payload.generated_at_utc);
    if (generatedDate) {
      const ageHours = (Date.now() - generatedDate.getTime()) / (1000 * 3600);
      if (ageHours > staleHours) staleWarning = `Data may be stale (${ageHours.toFixed(1)}h old)`;
    }
    setStatus(statusEl, payload, staleWarning);

    const precipLevels = payload.precip || {};
    const precipLevel = precipLevels.surface || precipLevels[Object.keys(precipLevels)[0]];
    if (precipEl && precipLevel) {
      const traces = [];
      const band = buildBandTrace(precipLevel.p10, precipLevel.p90, 'p10-p90', 'rgba(27,99,198,0.16)');
      if (band) traces.push(band);
      traces.push(buildLineTrace(precipLevel.p50, 'p50', colors.accent));
      traces.push(buildLineTrace(precipLevel.mean, 'mean', '#fb923c', 'dash'));
      Plotly.react(
        precipEl,
        traces,
        layout('GEFS Precipitation (Surface)', `APCP (${precipLevel.units || ''})`, colors),
        { responsive: true, displayModeBar: false }
      );
    }

    if (soilEl) {
      const levels = Object.keys(payload.soil_moisture || {}).sort((a, b) => levelSortKey(a) - levelSortKey(b));
      const palette = ['#1b63c6', '#0ea5e9', '#22c55e', '#f97316', '#ef4444'];
      const traces = [];
      levels.forEach((level, idx) => {
        const block = payload.soil_moisture[level];
        const band = buildBandTrace(block.p10, block.p90, `${level} p10-p90`, `rgba(14,165,233,${0.08 + idx * 0.03})`);
        if (band) traces.push(band);
        traces.push(buildLineTrace(block.p50, `${level} p50`, palette[idx % palette.length]));
      });
      Plotly.react(
        soilEl,
        traces,
        layout('GEFS Soil Moisture by Depth', 'SOILW (fraction)', colors),
        { responsive: true, displayModeBar: false }
      );
    }
  }

  async function initOne(container) {
    if (!window.Plotly) return;
    const statusEl = container.querySelector('.gefs-forecast-status');
    const url = container.dataset.gefsUrl || '/assets/data/forecasts/gefs_big_trees_latest.json';
    const refreshMinutes = Math.max(1, numberOrNull(container.dataset.refreshMin) || 60);
    const refreshMs = refreshMinutes * 60 * 1000;
    let inFlight = false;

    async function refreshOnce() {
      if (inFlight) return;
      inFlight = true;
      try {
        const response = await fetch(buildFetchUrl(url), { cache: 'no-store' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        if (!payload || typeof payload !== 'object') throw new Error('Invalid JSON payload');
        renderPanel(container, payload);
      } catch (err) {
        if (statusEl) {
          statusEl.textContent = `GEFS forecast unavailable (${err.message || 'unknown error'})`;
          statusEl.classList.add('plot-status--error');
        }
        const precipEl = container.querySelector('.gefs-forecast-precip');
        const soilEl = container.querySelector('.gefs-forecast-soil');
        if (precipEl && window.Plotly) Plotly.purge(precipEl);
        if (soilEl && window.Plotly) Plotly.purge(soilEl);
      } finally {
        inFlight = false;
      }
    }

    await refreshOnce();
    window.setInterval(refreshOnce, refreshMs);
  }

  function init() {
    const panels = document.querySelectorAll('.gefs-forecast-panel');
    if (!panels.length) return;
    panels.forEach((panel) => {
      initOne(panel);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
