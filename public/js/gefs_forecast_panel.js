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

  function latestPointDate(pointGroups) {
    let latest = null;
    (pointGroups || []).forEach((points) => {
      if (!Array.isArray(points)) return;
      points.forEach((point) => {
        if (!point || !point.t) return;
        const ts = parseDate(point.t);
        if (!ts) return;
        if (!latest || ts > latest) latest = ts;
      });
    });
    return latest;
  }

  function buildXRange(initDate, windowDays, pointGroups) {
    if (!initDate) return null;
    const start = new Date(initDate.getTime() - windowDays * 24 * 3600 * 1000);
    const latest = latestPointDate(pointGroups);
    const fallbackEnd = new Date(initDate.getTime() + 24 * 3600 * 1000);
    const end = latest && latest > initDate ? latest : fallbackEnd;
    return [start, end];
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

  function buildLineTrace(points, name, color, dash, options) {
    const series = seriesToXY(points);
    if (!series.x.length) return null;
    const opts = options || {};
    return {
      x: series.x,
      y: series.y,
      type: 'scatter',
      mode: 'lines',
      name,
      opacity: opts.opacity === undefined ? 1 : opts.opacity,
      line: { color, width: opts.width || 2, dash: dash || 'solid' },
      showlegend: opts.showlegend === undefined ? true : Boolean(opts.showlegend)
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

  function layout(title, yTitle, colors, options) {
    const opts = options || {};
    const chartLayout = {
      margin: { l: 56, r: 18, t: 26, b: 48 },
      title: { text: title, font: { size: 14, color: colors.text } },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: { color: colors.text, family: 'Source Sans Pro, Helvetica, Arial, sans-serif' },
      xaxis: { type: 'date', title: 'Valid time', gridcolor: colors.grid },
      yaxis: { title: yTitle, gridcolor: colors.grid },
      legend: { orientation: 'h', y: 1.14, x: 0 }
    };
    if (Array.isArray(opts.xRange) && opts.xRange.length === 2) {
      chartLayout.xaxis.range = opts.xRange;
    }
    if (opts.initTime) {
      chartLayout.shapes = [
        {
          type: 'line',
          xref: 'x',
          yref: 'paper',
          x0: opts.initTime,
          x1: opts.initTime,
          y0: 0,
          y1: 1,
          line: { color: '#64748b', width: 1, dash: 'dot' }
        }
      ];
    }
    return chartLayout;
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
    const retroWindowDays = payload && Number.isFinite(Number(payload.observation_window_days))
      ? Number(payload.observation_window_days)
      : null;
    const observed = payload && payload.observed_retrospective && typeof payload.observed_retrospective === 'object'
      ? payload.observed_retrospective
      : null;
    const observedPoints = observed
      ? [
          observed.daily_avg_ppt,
          observed.daily_avg_soil_ERA5,
          observed.daily_avg_soil_NWM_SOIL_M,
          observed.daily_avg_soil_NWM_SOIL_W
        ]
          .reduce((acc, series) => acc + (Array.isArray(series) ? series.length : 0), 0)
      : 0;
    const retroText = retroWindowDays ? `Retrospective window: ${retroWindowDays}d` : '';
    const observedText = observedPoints > 0 ? `Observed context points: ${observedPoints}` : '';
    el.textContent = `Init: ${initTime} | Generated: ${generated} | Members: ${members} | ${missing}${retroText ? ` | ${retroText}` : ''}${observedText ? ` | ${observedText}` : ''}${warning ? ` | ${warning}` : ''}`;
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
    const initDate = parseDate(payload.init_time_utc);
    const observationWindowDays = Math.max(
      1,
      numberOrNull(container.dataset.observationWindowDays) ||
        numberOrNull(payload.observation_window_days) ||
        20
    );
    const retrospective = payload.retrospective || {};
    const observedRetro = payload.observed_retrospective || {};

    const staleHours = numberOrNull(container.dataset.staleHours) ?? numberOrNull(payload.stale_after_hours) ?? 12;
    let staleWarning = '';
    const generatedDate = parseDate(payload.generated_at_utc);
    if (generatedDate) {
      const ageHours = (Date.now() - generatedDate.getTime()) / (1000 * 3600);
      if (ageHours > staleHours) staleWarning = `Data may be stale (${ageHours.toFixed(1)}h old)`;
    }
    setStatus(statusEl, payload, staleWarning);

    const precipLevels = payload.precip || {};
    const precipLevelName = precipLevels.surface ? 'surface' : Object.keys(precipLevels)[0];
    const precipLevel = precipLevelName ? precipLevels[precipLevelName] : null;
    if (precipEl && precipLevel) {
      const traces = [];
      const observedPrecip = observedRetro.daily_avg_ppt;
      const hasObservedPrecip = Array.isArray(observedPrecip) && observedPrecip.length > 0;
      const retroPrecip = ((retrospective.precip || {})[precipLevelName]) || null;
      if (hasObservedPrecip) {
        const obsTrace = buildLineTrace(observedPrecip, 'observed ppt (PRISM)', '#111827', 'solid', { width: 2.2 });
        if (obsTrace) traces.push(obsTrace);
      } else if (retroPrecip) {
        const retroBand = buildBandTrace(
          retroPrecip.p10,
          retroPrecip.p90,
          'retrospective p10-p90',
          'rgba(100,116,139,0.18)'
        );
        if (retroBand) traces.push(retroBand);
        const retroP50 = buildLineTrace(retroPrecip.p50, 'retrospective p50', '#475569', 'dash', { width: 1.8 });
        if (retroP50) traces.push(retroP50);
        const retroMean = buildLineTrace(retroPrecip.mean, 'retrospective mean', '#64748b', 'dot', { width: 1.6 });
        if (retroMean) traces.push(retroMean);
      }
      const band = buildBandTrace(precipLevel.p10, precipLevel.p90, 'p10-p90', 'rgba(27,99,198,0.16)');
      if (band) traces.push(band);
      const p50Trace = buildLineTrace(precipLevel.p50, 'p50', colors.accent);
      if (p50Trace) traces.push(p50Trace);
      const meanTrace = buildLineTrace(precipLevel.mean, 'mean', '#fb923c', 'dash');
      if (meanTrace) traces.push(meanTrace);
      const precipXRange = buildXRange(
        initDate,
        observationWindowDays,
        [
          observedPrecip,
          precipLevel.p10, precipLevel.p50, precipLevel.p90, precipLevel.mean,
          retroPrecip && retroPrecip.p10, retroPrecip && retroPrecip.p50,
          retroPrecip && retroPrecip.p90, retroPrecip && retroPrecip.mean
        ]
      );
      Plotly.react(
        precipEl,
        traces,
        layout(
          'GEFS Precipitation (Surface)',
          `APCP (${precipLevel.units || ''})`,
          colors,
          { xRange: precipXRange, initTime: initDate }
        ),
        { responsive: true, displayModeBar: false }
      );
    }

    if (soilEl) {
      const levels = Object.keys(payload.soil_moisture || {}).sort((a, b) => levelSortKey(a) - levelSortKey(b));
      const palette = ['#1b63c6', '#0ea5e9', '#22c55e', '#f97316', '#ef4444'];
      const traces = [];
      const pointGroups = [];
      const observedSoilEra5 = observedRetro.daily_avg_soil_ERA5;
      const observedSoilNwmM = observedRetro.daily_avg_soil_NWM_SOIL_M;
      const observedSoilNwmW = observedRetro.daily_avg_soil_NWM_SOIL_W;
      const hasObservedSoil = [observedSoilEra5, observedSoilNwmM, observedSoilNwmW]
        .some((series) => Array.isArray(series) && series.length > 0);
      const obsEra5Trace = buildLineTrace(observedSoilEra5, 'observed soil ERA5', '#0f766e', 'solid', { width: 2.1 });
      if (obsEra5Trace) traces.push(obsEra5Trace);
      const obsNwmMTrace = buildLineTrace(observedSoilNwmM, 'observed soil NWM SOIL_M', '#7c3aed', 'solid', { width: 1.8 });
      if (obsNwmMTrace) traces.push(obsNwmMTrace);
      const obsNwmWTrace = buildLineTrace(observedSoilNwmW, 'observed soil NWM SOIL_W', '#be185d', 'solid', { width: 1.8 });
      if (obsNwmWTrace) traces.push(obsNwmWTrace);
      pointGroups.push(observedSoilEra5, observedSoilNwmM, observedSoilNwmW);
      levels.forEach((level, idx) => {
        const block = payload.soil_moisture[level];
        const retroLevel = ((retrospective.soil_moisture || {})[level]) || null;
        if (!hasObservedSoil && retroLevel && retroLevel.p50) {
          const retroTrace = buildLineTrace(
            retroLevel.p50,
            `${level} retrospective p50`,
            palette[idx % palette.length],
            'dot',
            { width: 1.5, opacity: 0.55, showlegend: false }
          );
          if (retroTrace) traces.push(retroTrace);
          pointGroups.push(retroLevel.p50);
        }
        const band = buildBandTrace(block.p10, block.p90, `${level} p10-p90`, `rgba(14,165,233,${0.08 + idx * 0.03})`);
        if (band) traces.push(band);
        const soilP50 = buildLineTrace(block.p50, `${level} p50`, palette[idx % palette.length]);
        if (soilP50) traces.push(soilP50);
        pointGroups.push(block.p10, block.p50, block.p90);
      });
      const soilXRange = buildXRange(initDate, observationWindowDays, pointGroups);
      Plotly.react(
        soilEl,
        traces,
        layout(
          'GEFS Soil Moisture by Depth',
          'SOILW (fraction)',
          colors,
          { xRange: soilXRange, initTime: initDate }
        ),
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
