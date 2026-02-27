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
    if (typeof value === 'string' && value.trim() === '') return null;
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

  function parseDailyTimestamp(value) {
    if (!value) return null;
    const raw = String(value).trim();
    if (!raw) return null;
    const isoDay = /^\d{4}-\d{2}-\d{2}$/;
    if (isoDay.test(raw)) {
      return parseDate(`${raw}T00:00:00Z`);
    }
    return parseDate(raw);
  }

  function parseSimpleCsv(text) {
    if (typeof text !== 'string' || !text.trim()) return [];
    const lines = text.split(/\r?\n/).filter((line) => line.trim().length > 0);
    if (lines.length < 2) return [];
    const headers = lines[0].split(',').map((value) => String(value || '').trim());
    const idx = Object.create(null);
    headers.forEach((name, i) => { idx[name] = i; });
    if (idx.timestamp === undefined) return [];
    const rows = [];
    for (let i = 1; i < lines.length; i += 1) {
      const cols = lines[i].split(',');
      const timestamp = cols[idx.timestamp] ? String(cols[idx.timestamp]).trim() : '';
      if (!timestamp) continue;
      rows.push({
        timestamp,
        daily_avg_ppt: idx.daily_avg_ppt === undefined ? '' : (cols[idx.daily_avg_ppt] || '').trim(),
        daily_avg_soil_ERA5: idx.daily_avg_soil_ERA5 === undefined ? '' : (cols[idx.daily_avg_soil_ERA5] || '').trim(),
        daily_avg_soil_NWM_SOIL_M: idx.daily_avg_soil_NWM_SOIL_M === undefined ? '' : (cols[idx.daily_avg_soil_NWM_SOIL_M] || '').trim(),
        daily_avg_soil_NWM_SOIL_W: idx.daily_avg_soil_NWM_SOIL_W === undefined ? '' : (cols[idx.daily_avg_soil_NWM_SOIL_W] || '').trim()
      });
    }
    return rows;
  }

  function buildObservedRetrospectiveFromCsv(rows, initDate, observationWindowDays, sourceCsv) {
    if (!Array.isArray(rows) || !initDate) return null;
    const startDate = new Date(initDate.getTime() - observationWindowDays * 24 * 3600 * 1000);
    const filtered = rows
      .map((row) => {
        const ts = parseDailyTimestamp(row.timestamp);
        if (!ts) return null;
        if (ts < startDate || ts >= initDate) return null;
        return { ...row, _date: ts };
      })
      .filter(Boolean)
      .sort((a, b) => a._date - b._date);
    if (!filtered.length) return null;

    function toSeries(column) {
      const series = [];
      filtered.forEach((row) => {
        const num = numberOrNull(row[column]);
        if (num === null) return;
        series.push({ t: row._date.toISOString(), v: num });
      });
      return series;
    }

    return {
      window_days: observationWindowDays,
      start_utc: startDate.toISOString(),
      end_utc: initDate.toISOString(),
      source_csv: sourceCsv,
      daily_avg_ppt: toSeries('daily_avg_ppt'),
      daily_avg_soil_ERA5: toSeries('daily_avg_soil_ERA5'),
      daily_avg_soil_NWM_SOIL_M: toSeries('daily_avg_soil_NWM_SOIL_M'),
      daily_avg_soil_NWM_SOIL_W: toSeries('daily_avg_soil_NWM_SOIL_W')
    };
  }

  function hasObservedRetrospective(payload) {
    if (!payload || typeof payload !== 'object') return false;
    const observed = payload.observed_retrospective;
    if (!observed || typeof observed !== 'object') return false;
    const keys = [
      'daily_avg_ppt',
      'daily_avg_soil_ERA5',
      'daily_avg_soil_NWM_SOIL_M',
      'daily_avg_soil_NWM_SOIL_W'
    ];
    return keys.some((key) => Array.isArray(observed[key]) && observed[key].length > 0);
  }

  async function attachObservedRetrospective(container, payload) {
    if (!payload || typeof payload !== 'object') return payload;
    if (hasObservedRetrospective(payload)) return payload;
    const initDate = parseDate(payload.init_time_utc);
    if (!initDate) return payload;
    const observationWindowDays = Math.max(
      1,
      numberOrNull(container.dataset.observationWindowDays) ||
        numberOrNull(payload.observation_window_days) ||
        20
    );
    const csvUrl = container.dataset.observedCsvUrl || '/climate_daily_ppt_soil.csv';
    try {
      const response = await fetch(buildFetchUrl(csvUrl), { cache: 'no-store' });
      if (!response.ok) return payload;
      const text = await response.text();
      const rows = parseSimpleCsv(text);
      const observed = buildObservedRetrospectiveFromCsv(rows, initDate, observationWindowDays, csvUrl);
      if (observed) payload.observed_retrospective = observed;
    } catch (err) {
      // Keep panel resilient when optional observed CSV is unavailable.
    }
    return payload;
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

  function buildBandTrace(low, high, name, color, options) {
    const opts = options || {};
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
      legendgroup: opts.legendGroup || undefined,
      showlegend: opts.showLegend === undefined ? false : Boolean(opts.showLegend)
    };
  }

  function buildLineTrace(points, name, color, dash, options) {
    const series = seriesToXY(points);
    if (!series.x.length) return null;
    const opts = options || {};
    const unitSuffix = opts.unit ? ` ${opts.unit}` : '';
    const valueFormat = opts.valueFormat || '.2f';
    const hoverLabel = opts.hoverLabel || name;
    const mode = opts.mode || 'lines';
    const trace = {
      x: series.x,
      y: series.y,
      type: 'scatter',
      mode,
      name,
      legendgroup: opts.legendGroup || undefined,
      opacity: opts.opacity === undefined ? 1 : opts.opacity,
      line: { color, width: opts.width || 2, dash: dash || 'solid' },
      hovertemplate: `%{x|%b %d, %Y %H:%M UTC}<br>${hoverLabel}: %{y:${valueFormat}}${unitSuffix}<extra></extra>`,
      showlegend: opts.showlegend === undefined ? true : Boolean(opts.showlegend)
    };
    if (mode.indexOf('markers') !== -1) {
      trace.marker = {
        color,
        size: opts.markerSize || 4.5,
        symbol: opts.markerSymbol || 'circle-open'
      };
    }
    return trace;
  }

  function getThemeColors() {
    const styles = getComputedStyle(document.documentElement);
    return {
      text: styles.getPropertyValue('--text-color').trim() || '#1f2933',
      grid: styles.getPropertyValue('--border-color').trim() || '#e2e8f0',
      accent: styles.getPropertyValue('--accent-color').trim() || '#1b63c6',
      muted: styles.getPropertyValue('--text-subtle').trim() || '#64748b',
      surface: styles.getPropertyValue('--surface-1').trim() || '#ffffff'
    };
  }

  function layout(title, yTitle, colors, options) {
    const opts = options || {};
    const hasTitle = typeof title === 'string' && title.trim().length > 0;
    const chartLayout = {
      margin: { l: 60, r: 20, t: hasTitle ? 42 : 20, b: 52 },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: { color: colors.text, family: 'Source Sans Pro, Helvetica, Arial, sans-serif' },
      hovermode: 'x unified',
      hoverlabel: {
        bgcolor: colors.surface,
        bordercolor: colors.grid,
        font: { color: colors.text, size: 11 }
      },
      xaxis: {
        type: 'date',
        title: 'Valid time (UTC)',
        gridcolor: colors.grid,
        showline: true,
        linecolor: colors.grid,
        tickformat: '%b %d',
        showspikes: true,
        spikemode: 'across',
        spikesnap: 'cursor',
        spikedash: 'dot',
        automargin: true
      },
      yaxis: {
        title: yTitle,
        gridcolor: colors.grid,
        showline: true,
        linecolor: colors.grid,
        automargin: true
      },
      legend: {
        orientation: 'h',
        y: opts.legendY === undefined ? 1.14 : opts.legendY,
        x: 0,
        font: { size: 11, color: colors.text },
        itemclick: 'toggle',
        itemdoubleclick: 'toggleothers'
      }
    };
    if (hasTitle) {
      chartLayout.title = { text: title, font: { size: 15, color: colors.text }, x: 0.01, xanchor: 'left' };
    }
    if (Array.isArray(opts.xRange) && opts.xRange.length === 2) {
      chartLayout.xaxis.range = opts.xRange;
    }
    if (opts.yTickFormat) {
      chartLayout.yaxis.tickformat = opts.yTickFormat;
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
      chartLayout.annotations = [
        {
          xref: 'x',
          x: opts.initTime,
          yref: 'paper',
          y: 1.03,
          text: 'Forecast init',
          showarrow: false,
          font: { size: 11, color: colors.muted },
          xanchor: 'left',
          yanchor: 'bottom'
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
    const observedPptCount = observed && Array.isArray(observed.daily_avg_ppt) ? observed.daily_avg_ppt.length : 0;
    const observedEra5Count = observed && Array.isArray(observed.daily_avg_soil_ERA5) ? observed.daily_avg_soil_ERA5.length : 0;
    const observedNwmMCount = observed && Array.isArray(observed.daily_avg_soil_NWM_SOIL_M) ? observed.daily_avg_soil_NWM_SOIL_M.length : 0;
    const observedNwmWCount = observed && Array.isArray(observed.daily_avg_soil_NWM_SOIL_W) ? observed.daily_avg_soil_NWM_SOIL_W.length : 0;
    const retroText = retroWindowDays ? `Retrospective window: ${retroWindowDays}d` : '';
    const observedText = `Obs points (ppt/ERA5/NWM_M/NWM_W): ${observedPptCount}/${observedEra5Count}/${observedNwmMCount}/${observedNwmWCount}`;
    el.textContent = `Init: ${initTime} | Generated: ${generated} | Members: ${members} | ${missing}${retroText ? ` | ${retroText}` : ''} | ${observedText}${warning ? ` | ${warning}` : ''}`;
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
      const precipUnits = precipLevel.units || '';
      const observedPrecip = observedRetro.daily_avg_ppt;
      const hasObservedPrecip = Array.isArray(observedPrecip) && observedPrecip.length > 0;
      const retroPrecip = ((retrospective.precip || {})[precipLevelName]) || null;
      if (hasObservedPrecip) {
        const obsTrace = buildLineTrace(
          observedPrecip,
          'Observed PRISM',
          '#0f766e',
          'solid',
          { width: 2.3, unit: precipUnits, valueFormat: '.2f', hoverLabel: 'Observed PRISM' }
        );
        if (obsTrace) traces.push(obsTrace);
      } else if (retroPrecip) {
        const retroBand = buildBandTrace(
          retroPrecip.p10,
          retroPrecip.p90,
          'Retrospective p10-p90',
          'rgba(100,116,139,0.16)',
          { showLegend: true, legendGroup: 'precip_retro' }
        );
        if (retroBand) traces.push(retroBand);
        const retroP50 = buildLineTrace(
          retroPrecip.p50,
          'Retrospective p50',
          '#475569',
          'dash',
          {
            width: 1.8,
            unit: precipUnits,
            valueFormat: '.2f',
            hoverLabel: 'Retrospective p50',
            legendGroup: 'precip_retro'
          }
        );
        if (retroP50) traces.push(retroP50);
        const retroMean = buildLineTrace(
          retroPrecip.mean,
          'Retrospective mean',
          '#64748b',
          'dot',
          {
            width: 1.6,
            unit: precipUnits,
            valueFormat: '.2f',
            hoverLabel: 'Retrospective mean',
            legendGroup: 'precip_retro'
          }
        );
        if (retroMean) traces.push(retroMean);
      }
      const band = buildBandTrace(
        precipLevel.p10,
        precipLevel.p90,
        'GEFS p10-p90',
        'rgba(29,78,216,0.15)',
        { showLegend: true, legendGroup: 'precip_forecast' }
      );
      if (band) traces.push(band);
      const p50Trace = buildLineTrace(
        precipLevel.p50,
        'GEFS p50',
        colors.accent,
        'solid',
        {
          width: 2.2,
          unit: precipUnits,
          valueFormat: '.2f',
          hoverLabel: 'GEFS p50',
          legendGroup: 'precip_forecast'
        }
      );
      if (p50Trace) traces.push(p50Trace);
      const meanTrace = buildLineTrace(
        precipLevel.mean,
        'GEFS mean',
        '#ea580c',
        'dash',
        {
          width: 1.9,
          unit: precipUnits,
          valueFormat: '.2f',
          hoverLabel: 'GEFS mean',
          legendGroup: 'precip_forecast'
        }
      );
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
          '',
          `APCP (${precipLevel.units || ''})`,
          colors,
          { xRange: precipXRange, initTime: initDate, yTickFormat: '.1f', legendY: 1.16 }
        ),
        { responsive: true, displayModeBar: false }
      );
    }

    if (soilEl) {
      const levels = Object.keys(payload.soil_moisture || {}).sort((a, b) => levelSortKey(a) - levelSortKey(b));
      const palette = ['#1d4ed8', '#0284c7', '#16a34a', '#f59e0b', '#dc2626'];
      const traces = [];
      const pointGroups = [];
      const observedSoilEra5 = observedRetro.daily_avg_soil_ERA5;
      const observedSoilNwmM = observedRetro.daily_avg_soil_NWM_SOIL_M;
      const observedSoilNwmW = observedRetro.daily_avg_soil_NWM_SOIL_W;
      const hasObservedSoil = [observedSoilEra5, observedSoilNwmM, observedSoilNwmW]
        .some((series) => Array.isArray(series) && series.length > 0);
      const obsEra5Trace = buildLineTrace(
        observedSoilEra5,
        'Observed ERA5 swvl1',
        '#0f766e',
        'solid',
        { width: 2.2, valueFormat: '.3f', hoverLabel: 'Observed ERA5 swvl1', legendGroup: 'soil_obs' }
      );
      if (obsEra5Trace) traces.push(obsEra5Trace);
      const obsNwmMTrace = buildLineTrace(
        observedSoilNwmM,
        'Observed NWM SOIL_M',
        '#7c3aed',
        'solid',
        { width: 1.8, valueFormat: '.3f', hoverLabel: 'Observed NWM SOIL_M', legendGroup: 'soil_obs' }
      );
      if (obsNwmMTrace) traces.push(obsNwmMTrace);
      const obsNwmWTrace = buildLineTrace(
        observedSoilNwmW,
        'Observed NWM SOIL_W',
        '#be185d',
        'solid',
        { width: 1.8, valueFormat: '.3f', hoverLabel: 'Observed NWM SOIL_W', legendGroup: 'soil_obs' }
      );
      if (obsNwmWTrace) traces.push(obsNwmWTrace);
      pointGroups.push(observedSoilEra5, observedSoilNwmM, observedSoilNwmW);
      levels.forEach((level, idx) => {
        const block = payload.soil_moisture[level];
        const retroLevel = ((retrospective.soil_moisture || {})[level]) || null;
        if (!hasObservedSoil && retroLevel && retroLevel.p50) {
          const retroTrace = buildLineTrace(
            retroLevel.p50,
            `Retrospective p50 · ${level}`,
            '#64748b',
            'dot',
            {
              width: 1.5,
              opacity: 0.7,
              showlegend: idx === 0,
              valueFormat: '.3f',
              hoverLabel: `Retrospective p50 · ${level}`,
              legendGroup: 'soil_retro'
            }
          );
          if (retroTrace) traces.push(retroTrace);
          pointGroups.push(retroLevel.p50);
        }
        const band = buildBandTrace(
          block.p10,
          block.p90,
          `${level} p10-p90`,
          `rgba(14,165,233,${0.07 + idx * 0.02})`,
          { showLegend: false, legendGroup: `soil_${idx}` }
        );
        if (band) traces.push(band);
        const soilP50 = buildLineTrace(
          block.p50,
          `GEFS p50 · ${level}`,
          palette[idx % palette.length],
          'solid',
          {
            width: 1.95,
            valueFormat: '.3f',
            hoverLabel: `GEFS p50 · ${level}`,
            legendGroup: `soil_${idx}`
          }
        );
        if (soilP50) traces.push(soilP50);
        pointGroups.push(block.p10, block.p50, block.p90);
      });
      const soilXRange = buildXRange(initDate, observationWindowDays, pointGroups);
      Plotly.react(
        soilEl,
        traces,
        layout(
          '',
          'SOILW (fraction)',
          colors,
          { xRange: soilXRange, initTime: initDate, yTickFormat: '.2f', legendY: 1.18 }
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
        let payload = await response.json();
        if (!payload || typeof payload !== 'object') throw new Error('Invalid JSON payload');
        payload = await attachObservedRetrospective(container, payload);
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
