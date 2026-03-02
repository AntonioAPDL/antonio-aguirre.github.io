(() => {
  'use strict';

  if (window.__usgsIvPlotInitialized) {
    return;
  }
  window.__usgsIvPlotInitialized = true;

  const DEFAULTS = {
    period: 'P20D',
    refreshMin: 15,
    timeoutSec: 20,
    mode: 'discharge',
    logY: false,
    observationWindowDays: 20,
    futureHorizonHours: 240
  };
  const ENDPOINT_BASE = 'https://waterservices.usgs.gov/nwis/iv/';
  const MAX_BACKOFF_MS = 60 * 60 * 1000;
  const MIN_CACHE_AGE_MS = 30 * 60 * 1000;
  const STORAGE_VERSION = 3;
  const CFS_TO_CMS = 0.0283168466;
  const CMS_TO_CFS = 1 / CFS_TO_CMS;
  const FORECAST_START_MARKER_STYLE = {
    color: '#111827',
    width: 1.4,
    dash: 'dash',
    label: 'Forecast start'
  };

  const instances = [];

  /**
   * Clamp a numeric value; fall back to a default when invalid.
   */
  function clampNumber(value, min, max, fallback) {
    if (!Number.isFinite(value)) return fallback;
    return Math.min(max, Math.max(min, value));
  }

  function parseNumber(raw, fallback) {
    if (raw === undefined || raw === null || raw === '') return fallback;
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function parseOptionalNumber(raw) {
    if (raw === undefined || raw === null || raw === '') return null;
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function parseBoolean(raw, fallback) {
    if (raw === undefined || raw === null || raw === '') return fallback;
    const value = String(raw).toLowerCase();
    if (value === 'true' || value === '1' || value === 'yes') return true;
    if (value === 'false' || value === '0' || value === 'no') return false;
    return fallback;
  }

  function formatDate(value) {
    if (!value) return '--';
    const date = value instanceof Date ? value : new Date(value);
    if (Number.isNaN(date.getTime())) return '--';
    try {
      return date.toLocaleString(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short'
      });
    } catch (err) {
      return date.toISOString();
    }
  }

  function normalizeUnits(unitCode) {
    if (!unitCode) return unitCode;
    const normalized = String(unitCode).trim().toLowerCase();
    if (normalized === 'ft3/s' || normalized === 'ft^3/s' || normalized === 'ft3s-1') {
      return 'cfs';
    }
    if (normalized === 'm3/s' || normalized === 'm^3/s' || normalized === 'm3 s-1' ||
        normalized === 'm^3 s-1' || normalized === 'cms') {
      return 'cms';
    }
    if (normalized === 'ft') {
      return 'ft';
    }
    return unitCode;
  }

  function normalizeUnitCandidates(rawUnits) {
    const out = [];
    const pushIfValid = (candidate) => {
      const norm = normalizeUnits(candidate);
      if (norm === 'cfs' || norm === 'cms') {
        out.push(norm);
      }
    };

    if (Array.isArray(rawUnits)) {
      rawUnits.forEach((item) => pushIfValid(item));
    } else {
      pushIfValid(rawUnits);
    }
    return Array.from(new Set(out));
  }

  function convertFlowUnits(value, fromUnits, toUnits) {
    if (!Number.isFinite(value)) return NaN;
    const from = normalizeUnits(fromUnits);
    const to = normalizeUnits(toUnits);
    if (!from || !to) return NaN;
    if (from === to) return value;
    if (from === 'cfs' && to === 'cms') return value * CFS_TO_CMS;
    if (from === 'cms' && to === 'cfs') return value * CMS_TO_CFS;
    return NaN;
  }

  function parseFlowSeries(series, fromUnits, toUnits, logAxis) {
    if (!Array.isArray(series) || !series.length) return [];
    const out = [];
    series.forEach((row) => {
      if (!row || typeof row !== 'object') return;
      const timestamp = new Date(row.t);
      if (Number.isNaN(timestamp.getTime())) return;
      const rawValue = Number(row.v);
      if (!Number.isFinite(rawValue)) return;
      const converted = convertFlowUnits(rawValue, fromUnits, toUnits);
      if (!Number.isFinite(converted)) return;
      if (logAxis && converted <= 0) return;
      out.push({ x: timestamp, y: converted });
    });
    out.sort((a, b) => a.x - b.x);
    return out;
  }

  function createBandTraces(p10Points, p90Points, p50Points, label, unitLabel, colorLine, colorBand, legendRank) {
    const traces = [];
    const p10Ready = Array.isArray(p10Points) && p10Points.length;
    const p90Ready = Array.isArray(p90Points) && p90Points.length;
    const p50Ready = Array.isArray(p50Points) && p50Points.length;

    if (p10Ready && p90Ready) {
      traces.push({
        x: p90Points.map((p) => p.x),
        y: p90Points.map((p) => p.y),
        type: 'scatter',
        mode: 'lines',
        line: { width: 0, color: colorBand },
        hoverinfo: 'skip',
        showlegend: false,
        legendgroup: label
      });
      traces.push({
        x: p10Points.map((p) => p.x),
        y: p10Points.map((p) => p.y),
        type: 'scatter',
        mode: 'lines',
        line: { width: 0, color: colorBand },
        fill: 'tonexty',
        fillcolor: colorBand,
        name: `${label} p10-p90`,
        legendrank: legendRank,
        legendgroup: label,
        hovertemplate: `%{x|%b %d, %Y %H:%M UTC}<br>${label} p10-p90: %{y:.2f} ${unitLabel}<extra></extra>`
      });
    }

    if (p50Ready) {
      traces.push({
        x: p50Points.map((p) => p.x),
        y: p50Points.map((p) => p.y),
        type: 'scatter',
        mode: 'lines',
        name: `${label} p50`,
        legendrank: legendRank + 1,
        legendgroup: label,
        line: { color: colorLine, width: 2.0 },
        hovertemplate: `%{x|%b %d, %Y %H:%M UTC}<br>${label} p50: %{y:.2f} ${unitLabel}<extra></extra>`
      });
    }
    return traces;
  }

  function buildForecastStartMarker(forecastStart, colors) {
    if (!(forecastStart instanceof Date) || Number.isNaN(forecastStart.getTime())) {
      return { shapes: [], annotations: [] };
    }
    return {
      shapes: [
        {
          type: 'line',
          xref: 'x',
          x0: forecastStart,
          x1: forecastStart,
          yref: 'paper',
          y0: 0,
          y1: 1,
          line: {
            color: FORECAST_START_MARKER_STYLE.color,
            width: FORECAST_START_MARKER_STYLE.width,
            dash: FORECAST_START_MARKER_STYLE.dash
          }
        }
      ],
      annotations: [
        {
          xref: 'x',
          x: forecastStart,
          yref: 'paper',
          y: 1,
          xanchor: 'left',
          yanchor: 'bottom',
          text: FORECAST_START_MARKER_STYLE.label,
          showarrow: false,
          font: {
            size: 11,
            color: FORECAST_START_MARKER_STYLE.color
          },
          bgcolor: 'rgba(255, 255, 255, 0.6)',
          bordercolor: 'rgba(255, 255, 255, 0.0)',
          borderpad: 2
        }
      ]
    };
  }

  function buildForecastOverlay(payload, observedUnits, logAxis) {
    const traces = [];
    const extentPoints = [];
    const noteParts = [];
    let warning = null;

    if (!payload || typeof payload !== 'object') {
      return { traces, extentPoints, note: null, warning: null, forecastStart: null };
    }
    const ranges = payload.ranges && typeof payload.ranges === 'object' ? payload.ranges : null;
    if (!ranges) {
      return { traces, extentPoints, note: null, warning: null, forecastStart: null };
    }

    const observedFlowUnits = normalizeUnits(observedUnits);
    if (observedFlowUnits !== 'cfs' && observedFlowUnits !== 'cms') {
      return {
        traces,
        extentPoints,
        note: null,
        warning: 'Forecast overlay skipped: unsupported observed discharge units.',
        forecastStart: null
      };
    }

    const forecastUnitCandidates = normalizeUnitCandidates(payload.units);
    let forecastUnits = null;
    if (forecastUnitCandidates.includes(observedFlowUnits)) {
      forecastUnits = observedFlowUnits;
    } else if (forecastUnitCandidates.length) {
      forecastUnits = forecastUnitCandidates[0];
      if (forecastUnits !== observedFlowUnits) {
        noteParts.push(`Forecast converted from ${forecastUnits} to ${observedFlowUnits}`);
      }
    } else {
      warning = 'Forecast overlay skipped: forecast units missing or unsupported.';
      return { traces, extentPoints, note: null, warning, forecastStart: null };
    }

    const medium = ranges.medium_range && typeof ranges.medium_range === 'object' ? ranges.medium_range : {};
    const longRange = ranges.long_range && typeof ranges.long_range === 'object' ? ranges.long_range : {};

    const mediumP10 = parseFlowSeries(medium.p10, forecastUnits, observedFlowUnits, logAxis);
    const mediumP50 = parseFlowSeries(medium.p50, forecastUnits, observedFlowUnits, logAxis);
    const mediumP90 = parseFlowSeries(medium.p90, forecastUnits, observedFlowUnits, logAxis);
    const longP10 = parseFlowSeries(longRange.p10, forecastUnits, observedFlowUnits, logAxis);
    const longP50 = parseFlowSeries(longRange.p50, forecastUnits, observedFlowUnits, logAxis);
    const longP90 = parseFlowSeries(longRange.p90, forecastUnits, observedFlowUnits, logAxis);
    const ensembleSeries = [mediumP10, mediumP50, mediumP90, longP10, longP50, longP90];
    let forecastStart = null;
    ensembleSeries.forEach((series) => {
      if (!Array.isArray(series) || !series.length) return;
      const first = series[0].x;
      if (!(first instanceof Date) || Number.isNaN(first.getTime())) return;
      if (!forecastStart || first < forecastStart) {
        forecastStart = first;
      }
    });

    traces.push(
      ...createBandTraces(
        mediumP10,
        mediumP90,
        mediumP50,
        'NWS medium',
        observedFlowUnits,
        '#5844c6',
        'rgba(88, 68, 198, 0.18)',
        20
      ),
      ...createBandTraces(
        longP10,
        longP90,
        longP50,
        'NWS long',
        observedFlowUnits,
        '#6f2d91',
        'rgba(111, 45, 145, 0.16)',
        30
      )
    );

    [mediumP10, mediumP50, mediumP90, longP10, longP50, longP90].forEach((series) => {
      series.forEach((point) => extentPoints.push(point));
    });

    if (traces.length) {
      noteParts.unshift('NWS ensemble overlay active');
    }
    return {
      traces,
      extentPoints,
      note: noteParts.length ? noteParts.join(' • ') : null,
      warning,
      forecastStart
    };
  }

  function getThemeColors() {
    const styles = getComputedStyle(document.documentElement);
    return {
      text: styles.getPropertyValue('--text-color').trim() || '#1f2933',
      grid: styles.getPropertyValue('--border-color').trim() || '#e2e8f0',
      line: styles.getPropertyValue('--accent-color').trim() || '#1b63c6',
      surface: styles.getPropertyValue('--surface-1').trim() || '#ffffff'
    };
  }

  function createError(kind, message, status) {
    const error = new Error(message);
    error.kind = kind;
    if (status) error.status = status;
    return error;
  }

  function getDataExtent(points, logAxis) {
    const values = points
      .map((point) => point.y)
      .filter((value) => Number.isFinite(value))
      .filter((value) => !logAxis || value > 0);
    if (!values.length) return null;
    return {
      min: Math.min(...values),
      max: Math.max(...values)
    };
  }

  function buildUrl(config) {
    const params = new URLSearchParams({
      format: 'json',
      sites: config.siteId,
      parameterCd: config.parameterCd,
      period: config.period,
      siteStatus: 'all'
    });
    return `${ENDPOINT_BASE}?${params.toString()}`;
  }

  function extractSeries(json) {
    const series = json && json.value && Array.isArray(json.value.timeSeries)
      ? json.value.timeSeries[0]
      : null;
    if (!series) {
      throw createError('schema', 'Unexpected response format (missing timeSeries).');
    }
    const values = series.values && series.values[0] && series.values[0].value;
    if (!Array.isArray(values) || !values.length) {
      throw createError('schema', 'No observations available for the requested period.');
    }
    const points = values
      .map((point) => {
        const numeric = parseFloat(point.value);
        if (!Number.isFinite(numeric)) return null;
        const timestamp = new Date(point.dateTime);
        if (Number.isNaN(timestamp.getTime())) return null;
        return {
          x: timestamp,
          y: numeric
        };
      })
      .filter(Boolean)
      .sort((a, b) => a.x - b.x);

    if (!points.length) {
      throw createError('schema', 'No numeric values available.');
    }

    return { series, points };
  }

  function buildLayout(yTitle, colors, yRange, shapes, logAxis, annotations, xRange) {
    const yaxis = {
      title: yTitle,
      gridcolor: colors.grid,
      zerolinecolor: colors.grid,
      showline: true,
      linecolor: colors.grid,
      automargin: true,
      type: logAxis ? 'log' : 'linear'
    };

    if (Array.isArray(yRange) && Number.isFinite(yRange[0]) && Number.isFinite(yRange[1])) {
      if (logAxis && yRange[0] > 0 && yRange[1] > 0) {
        yaxis.range = [Math.log10(yRange[0]), Math.log10(yRange[1])];
        yaxis.autorange = false;
      } else if (!logAxis) {
        yaxis.range = yRange;
        yaxis.autorange = false;
      }
    }

    const xaxis = {
      title: 'Date (UTC)',
      type: 'date',
      gridcolor: colors.grid,
      zerolinecolor: colors.grid,
      tickformat: '%b %d',
      showline: true,
      linecolor: colors.grid,
      showspikes: true,
      spikemode: 'across',
      spikesnap: 'cursor',
      spikedash: 'dot',
      automargin: true
    };

    if (Array.isArray(xRange) && xRange[0] && xRange[1]) {
      xaxis.range = xRange;
    }

    return {
      margin: { l: 60, r: 20, t: 20, b: 50 },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      hovermode: 'x unified',
      hoverlabel: {
        bgcolor: colors.surface,
        bordercolor: colors.grid,
        font: { color: colors.text, size: 11 }
      },
      shapes: shapes || [],
      annotations: annotations || [],
      font: {
        color: colors.text,
        family: 'Source Sans Pro, Helvetica, Arial, sans-serif'
      },
      xaxis: xaxis,
      yaxis: yaxis
    };
  }

  function buildTrace(points, units, colors) {
    const unitLabel = units ? ` ${units}` : '';
    return {
      x: points.map((p) => p.x),
      y: points.map((p) => p.y),
      type: 'scatter',
      mode: 'lines',
      name: 'Observed',
      showlegend: true,
      legendrank: 10,
      line: { color: colors.line, width: 2.6 },
      hovertemplate: `%{x|%b %d, %Y %H:%M UTC}<br>Observed: %{y:.2f}${unitLabel}<extra></extra>`
    };
  }

  function buildThresholdShapes(config, colors, yRange) {
    const shapes = [];
    const annotations = [];
    const minor = config.thresholdMinor;
    const moderate = config.thresholdModerate;
    const major = config.thresholdMajor;

    if (!Number.isFinite(minor) || !Number.isFinite(major)) {
      return { shapes, annotations };
    }

    if (Number.isFinite(moderate) && (moderate <= minor || major <= moderate)) {
      console.warn('[usgs-iv] Thresholds should be ordered minor < moderate < major.', config);
    } else if (major <= minor) {
      console.warn('[usgs-iv] Major threshold must exceed minor threshold.', config);
      return { shapes, annotations };
    }

    const yMin = Array.isArray(yRange) ? yRange[0] : null;
    const yMax = Array.isArray(yRange) ? yRange[1] : null;

    const bandMinor = 'rgba(242, 201, 76, 0.18)';
    const bandModerate = 'rgba(251, 146, 60, 0.18)';
    const bandMajor = 'rgba(220, 38, 38, 0.16)';
    const lineMinor = colors && colors.line ? colors.line : '#f2c94c';
    const lineModerate = '#fb923c';
    const lineMajor = '#dc2626';

    const bands = [];
    if (Number.isFinite(moderate)) {
      bands.push({ start: minor, end: moderate, color: bandMinor });
      bands.push({ start: moderate, end: major, color: bandModerate });
    } else {
      bands.push({ start: minor, end: major, color: bandMinor });
    }
    if (Number.isFinite(major)) {
      bands.push({ start: major, end: yMax, color: bandMajor });
    }

    bands.forEach((band) => {
      const lower = Number.isFinite(yMin) ? Math.max(yMin, band.start) : band.start;
      const upper = Number.isFinite(yMax) ? Math.min(yMax, band.end) : band.end;
      if (!Number.isFinite(lower) || !Number.isFinite(upper) || upper <= lower) return;
      shapes.push({
        type: 'rect',
        xref: 'paper',
        yref: 'y',
        x0: 0,
        x1: 1,
        y0: lower,
        y1: upper,
        fillcolor: band.color,
        line: { width: 0 },
        layer: 'below'
      });
    });

    shapes.push({
      type: 'line',
      xref: 'paper',
      x0: 0,
      x1: 1,
      yref: 'y',
      y0: minor,
      y1: minor,
      line: { color: lineMinor, width: 1.5, dash: 'dash' }
    });

    if (Number.isFinite(moderate)) {
      shapes.push({
        type: 'line',
        xref: 'paper',
        x0: 0,
        x1: 1,
        yref: 'y',
        y0: moderate,
        y1: moderate,
        line: { color: lineModerate, width: 1.5, dash: 'dash' }
      });
    }

    shapes.push({
      type: 'line',
      xref: 'paper',
      x0: 0,
      x1: 1,
      yref: 'y',
      y0: major,
      y1: major,
      line: { color: lineMajor, width: 1.5, dash: 'dash' }
    });

    const addLabel = (label, yValue, color) => {
      if (!Number.isFinite(yValue)) return;
      if (config.logY && yValue <= 0) return;
      annotations.push({
        xref: 'paper',
        x: 0.02,
        yref: 'y',
        y: yValue,
        text: label,
        showarrow: false,
        xanchor: 'left',
        yanchor: 'bottom',
        font: {
          size: 11,
          color: color
        },
        bgcolor: 'rgba(255, 255, 255, 0.6)',
        bordercolor: 'rgba(255, 255, 255, 0.0)',
        borderpad: 2
      });
    };

    addLabel('Minor flood', minor, lineMinor);
    if (Number.isFinite(moderate)) {
      addLabel('Moderate flood', moderate, lineModerate);
    }
    addLabel('Major flood', major, lineMajor);

    return { shapes, annotations };
  }

  function storageAvailable() {
    try {
      const key = '__usgs_iv_test__';
      window.localStorage.setItem(key, key);
      window.localStorage.removeItem(key);
      return true;
    } catch (err) {
      return false;
    }
  }

  const hasStorage = storageAvailable();

  /**
   * Handles a single USGS IV plot container.
   */
  class UsgsIvPlot {
    constructor(container) {
      this.container = container;
      this.config = this.readConfig(container);

      this.statusEl = container.querySelector('.plot-status');
      this.stageEl = container.querySelector('.plot-stage');
      this.chartEl = container.querySelector('.usgs-iv-plot__chart');
      this.skeletonEl = container.querySelector('.plot-skeleton');

      this.timerId = null;
      this.failCount = 0;
      this.inFlight = false;
      this.pendingRefresh = false;
      this.abortController = null;
      this.abortedForVisibility = false;
      this.lastSuccess = null;
      this.lastRenderData = null;

      this.storageKey = this.buildStorageKey();
    }

    readConfig(container) {
      const dataset = container.dataset || {};
      const refreshMin = parseNumber(dataset.refreshMin, DEFAULTS.refreshMin);
      const timeoutSec = parseNumber(dataset.timeoutSec, DEFAULTS.timeoutSec);
      const observationWindowDays = clampNumber(
        parseNumber(dataset.observationWindowDays, DEFAULTS.observationWindowDays),
        1,
        120,
        DEFAULTS.observationWindowDays
      );
      const futureHorizonHoursRaw = parseOptionalNumber(dataset.futureHorizonHours);
      const modeRaw = (dataset.mode || DEFAULTS.mode).toLowerCase();
      const mode = modeRaw === 'stage' ? 'stage' : 'discharge';
      const logY = parseBoolean(dataset.logY, DEFAULTS.logY);
      const yMin = parseOptionalNumber(dataset.yMin);
      const yMax = parseOptionalNumber(dataset.yMax);
      const parameterCd = dataset.parameter || (mode === 'stage' ? '00065' : '00060');
      const defaultLabel = mode === 'stage' ? 'Stage' : 'Discharge';
      const floodMinor = parseOptionalNumber(dataset.floodMinorCfs || dataset.thresholdMinor);
      const floodModerate = parseOptionalNumber(dataset.floodModerateCfs || dataset.thresholdModerate);
      const floodMajor = parseOptionalNumber(dataset.floodMajorCfs || dataset.thresholdMajor);
      const defaultForecastUrl = mode === 'discharge' ? '/assets/data/forecasts/big_trees_latest.json' : '';
      const forecastUrlRaw = (dataset.forecastUrl || defaultForecastUrl || '').trim();
      return {
        siteId: dataset.site,
        parameterCd: parameterCd,
        mode: mode,
        period: dataset.period || DEFAULTS.period,
        refreshMs: clampNumber(refreshMin, 1, 1440, DEFAULTS.refreshMin) * 60 * 1000,
        timeoutMs: clampNumber(timeoutSec, 5, 60, DEFAULTS.timeoutSec) * 1000,
        title: dataset.title || '',
        yLabel: dataset.ylabel || defaultLabel,
        yMin: yMin,
        yMax: yMax,
        thresholdMinor: floodMinor,
        thresholdModerate: floodModerate,
        thresholdMajor: floodMajor,
        forecastUrl: forecastUrlRaw,
        logY: logY,
        observationWindowDays: observationWindowDays,
        futureHorizonHours: Number.isFinite(futureHorizonHoursRaw)
          ? clampNumber(futureHorizonHoursRaw, 0, 720, DEFAULTS.futureHorizonHours)
          : null
      };
    }

    buildStorageKey() {
      const { siteId, parameterCd, period } = this.config;
      return `usgs-iv:${siteId || 'unknown'}:${parameterCd || 'unknown'}:${period || 'P30D'}:v${STORAGE_VERSION}`;
    }

    validate() {
      let valid = true;

      if (!this.config.siteId || !this.config.parameterCd) {
        console.warn('[usgs-iv] Missing data-site or data-parameter on plot container.', this.container);
        valid = false;
      }

      if (Number.isFinite(this.config.yMin) && Number.isFinite(this.config.yMax) &&
          this.config.yMax <= this.config.yMin) {
        console.warn('[usgs-iv] data-y-max must exceed data-y-min.', this.container);
      }

      if (this.config.logY && Number.isFinite(this.config.yMin) && this.config.yMin <= 0) {
        console.warn('[usgs-iv] data-y-min must be > 0 for log scale.', this.container);
      }

      if (Number.isFinite(this.config.thresholdMinor) && Number.isFinite(this.config.thresholdMajor) &&
          this.config.thresholdMajor <= this.config.thresholdMinor) {
        console.warn('[usgs-iv] data-threshold-major should exceed data-threshold-minor.', this.container);
      }

      if (Number.isFinite(this.config.thresholdModerate) &&
          Number.isFinite(this.config.thresholdMinor) &&
          Number.isFinite(this.config.thresholdMajor)) {
        if (this.config.thresholdModerate <= this.config.thresholdMinor ||
            this.config.thresholdModerate >= this.config.thresholdMajor) {
          console.warn('[usgs-iv] data-threshold-moderate should sit between minor and major.', this.container);
        }
      }
      if (this.config.logY) {
        ['thresholdMinor', 'thresholdModerate', 'thresholdMajor'].forEach((key) => {
          const value = this.config[key];
          if (Number.isFinite(value) && value <= 0) {
            console.warn('[usgs-iv] Thresholds must be > 0 for log scale.', this.container);
          }
        });
      }

      if (!this.statusEl) {
        console.warn('[usgs-iv] Missing .plot-status element. Creating one.', this.container);
        this.statusEl = document.createElement('div');
        this.statusEl.className = 'plot-status';
        this.statusEl.setAttribute('role', 'status');
        this.statusEl.setAttribute('aria-live', 'polite');
        this.container.prepend(this.statusEl);
      }

      if (!this.chartEl) {
        console.warn('[usgs-iv] Missing .usgs-iv-plot__chart element. Creating one.', this.container);
        this.chartEl = document.createElement('div');
        this.chartEl.className = 'usgs-iv-plot__chart';
        if (this.stageEl) {
          this.stageEl.appendChild(this.chartEl);
        } else {
          this.container.appendChild(this.chartEl);
        }
      }

      return valid;
    }

    init() {
      if (!this.validate()) {
        this.setStatus({ warning: 'Plot configuration missing required attributes.' });
        return;
      }

      this.renderFromCache();
      this.requestRefresh('init');
    }

    setStatus({ siteName, units, lastObs, lastRefresh, note, warning }) {
      if (!this.statusEl) return;

      const data = this.lastSuccess || {};
      const siteValue = siteName || data.siteName || this.config.title || 'USGS observations';
      const unitsValue = normalizeUnits(units || data.units);
      const lastObsValue = lastObs || data.lastObs;
      const lastRefreshValue = lastRefresh || data.lastRefresh;

      while (this.statusEl.firstChild) {
        this.statusEl.removeChild(this.statusEl.firstChild);
      }

      const titleEl = document.createElement('div');
      titleEl.className = 'plot-status__title';
      titleEl.textContent = siteValue;
      this.statusEl.appendChild(titleEl);

      const metaParts = [];
      if (unitsValue) metaParts.push(`Units: ${unitsValue}`);
      if (lastObsValue) metaParts.push(`Last obs: ${formatDate(lastObsValue)}`);
      if (lastRefreshValue) metaParts.push(`Updated: ${formatDate(lastRefreshValue)}`);
      if (note) metaParts.push(note);

      const metaEl = document.createElement('div');
      metaEl.className = 'plot-status__meta';
      metaEl.textContent = metaParts.length ? metaParts.join(' • ') : 'Loading data...';
      this.statusEl.appendChild(metaEl);

      if (warning) {
        const warnEl = document.createElement('div');
        warnEl.className = 'plot-status__warning';
        warnEl.textContent = warning;
        this.statusEl.appendChild(warnEl);
        this.statusEl.classList.add('plot-status--error');
      } else {
        this.statusEl.classList.remove('plot-status--error');
      }
    }

    setLoadedState(loaded) {
      this.container.classList.toggle('is-loaded', loaded);
    }

    updateAriaLabel(siteName) {
      if (!this.stageEl) return;
      const baseTitle = this.config.title || siteName || 'USGS IV plot';
      this.stageEl.setAttribute('aria-label', baseTitle);
    }

    resolveTimelineWindow(lastObs) {
      const obsDate = lastObs instanceof Date ? lastObs : new Date(lastObs);
      if (Number.isNaN(obsDate.getTime())) {
        return null;
      }

      const sharedWindow = window.__gefsTimelineWindow && typeof window.__gefsTimelineWindow === 'object'
        ? window.__gefsTimelineWindow
        : null;

      let observationWindowDays = this.config.observationWindowDays;
      if ((!Number.isFinite(observationWindowDays) || observationWindowDays <= 0) && sharedWindow) {
        const sharedDays = Number(sharedWindow.observationWindowDays);
        if (Number.isFinite(sharedDays) && sharedDays > 0) {
          observationWindowDays = sharedDays;
        }
      }
      if (!Number.isFinite(observationWindowDays) || observationWindowDays <= 0) {
        observationWindowDays = DEFAULTS.observationWindowDays;
      }

      let futureHorizonHours = this.config.futureHorizonHours;
      if ((!Number.isFinite(futureHorizonHours) || futureHorizonHours < 0) && sharedWindow) {
        const sharedHours = Number(sharedWindow.forecastHorizonHours);
        if (Number.isFinite(sharedHours) && sharedHours >= 0) {
          futureHorizonHours = sharedHours;
        }
      }
      if (!Number.isFinite(futureHorizonHours) || futureHorizonHours < 0) {
        futureHorizonHours = DEFAULTS.futureHorizonHours;
      }

      const start = new Date(obsDate.getTime() - observationWindowDays * 24 * 60 * 60 * 1000);
      const end = new Date(obsDate.getTime() + futureHorizonHours * 60 * 60 * 1000);
      if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || end <= start) {
        return null;
      }
      return [start, end];
    }

    renderPlot({ points, siteName, units, lastObs, lastRefresh, forecastPayload }, options = {}) {
      if (!window.Plotly) {
        this.setStatus({ warning: 'Plotly failed to load.' });
        return;
      }

      const colors = getThemeColors();
      const logAxis = this.config.logY;
      const displayUnits = normalizeUnits(units);
      const usablePoints = logAxis
        ? points.filter((point) => Number.isFinite(point.y) && point.y > 0)
        : points.slice();

      if (!usablePoints.length) {
        this.setStatus({ warning: 'No valid data available for plotting.' });
        return;
      }

      const forecastOverlay = (this.config.mode === 'discharge')
        ? buildForecastOverlay(forecastPayload, displayUnits, logAxis)
        : { traces: [], extentPoints: [], note: null, warning: null };

      const extentCandidates = usablePoints.concat(forecastOverlay.extentPoints || []);
      const extent = getDataExtent(extentCandidates, logAxis);
      let yMin = Number.isFinite(this.config.yMin) ? this.config.yMin : extent && extent.min;
      let yMax = Number.isFinite(this.config.yMax) ? this.config.yMax : extent && extent.max;

      if (logAxis && Number.isFinite(yMin) && yMin <= 0 && extent) {
        yMin = extent.min;
      }
      if (!Number.isFinite(yMin) || !Number.isFinite(yMax) || yMax <= yMin) {
        yMin = extent ? extent.min : null;
        yMax = extent ? extent.max : null;
      }

      const yRange = Number.isFinite(yMin) && Number.isFinite(yMax) ? [yMin, yMax] : null;
      const yTitleBase = displayUnits ? `${this.config.yLabel} (${displayUnits})` : this.config.yLabel;
      const yTitle = logAxis ? `${yTitleBase} (log scale)` : yTitleBase;
      const threshold = buildThresholdShapes(this.config, colors, yRange);
      const forecastStartMarker = buildForecastStartMarker(forecastOverlay.forecastStart, colors);
      const xRange = this.resolveTimelineWindow(lastObs);
      const baseTrace = buildTrace(usablePoints, displayUnits, colors);
      const traces = [baseTrace].concat(forecastOverlay.traces || []);
      const allShapes = (threshold.shapes || []).concat(forecastStartMarker.shapes || []);
      const allAnnotations = (threshold.annotations || []).concat(forecastStartMarker.annotations || []);

      Plotly.react(
        this.chartEl,
        traces,
        buildLayout(yTitle, colors, yRange, allShapes, logAxis, allAnnotations, xRange),
        { responsive: true, displayModeBar: false }
      );

      this.lastSuccess = {
        siteName,
        units: displayUnits,
        lastObs,
        lastRefresh
      };
      this.lastRenderData = {
        points: usablePoints.map((point) => ({ x: point.x, y: point.y })),
        siteName,
        units: displayUnits,
        lastObs,
        lastRefresh,
        forecastPayload
      };

      this.updateAriaLabel(siteName);
      this.setLoadedState(true);
      if (!options.silentStatus) {
        const notes = [options.note, forecastOverlay.note].filter(Boolean).join(' • ');
        const warning = options.warning || forecastOverlay.warning || null;
        this.setStatus({
          siteName,
          units: displayUnits,
          lastObs,
          lastRefresh,
          note: notes || undefined,
          warning: warning || undefined
        });
      }
    }

    rerenderForTheme() {
      if (!this.lastRenderData || !Array.isArray(this.lastRenderData.points) || !this.lastRenderData.points.length) {
        return;
      }
      try {
        this.renderPlot(this.lastRenderData, { silentStatus: true });
      } catch (err) {
        console.warn('[usgs-iv] Failed to rerender for theme update', err);
      }
    }

    rerenderForTimeline() {
      if (!this.lastRenderData || !Array.isArray(this.lastRenderData.points) || !this.lastRenderData.points.length) {
        return;
      }
      try {
        this.renderPlot(this.lastRenderData, { silentStatus: true });
      } catch (err) {
        console.warn('[usgs-iv] Failed to rerender for timeline update', err);
      }
    }

    /**
     * Render cached data if it is recent enough.
     */
    renderFromCache() {
      if (!hasStorage) return;

      try {
        const cachedRaw = window.localStorage.getItem(this.storageKey);
        if (!cachedRaw) return;
        const cached = JSON.parse(cachedRaw);
        if (!cached || cached.version !== STORAGE_VERSION) return;
        if (!Array.isArray(cached.points) || !cached.points.length) return;
        if (!cached.savedAt) return;

        const age = Date.now() - cached.savedAt;
        const maxAge = Math.max(this.config.refreshMs * 4, MIN_CACHE_AGE_MS);
        if (age > maxAge) return;

        const points = cached.points
          .map((point) => {
            const timestamp = new Date(point[0]);
            const value = Number(point[1]);
            if (Number.isNaN(timestamp.getTime()) || !Number.isFinite(value)) return null;
            return { x: timestamp, y: value };
          })
          .filter(Boolean);

        if (!points.length) return;

        this.renderPlot(
          {
            points,
            siteName: cached.siteName,
            units: cached.units,
            lastObs: points[points.length - 1].x,
            lastRefresh: new Date(cached.savedAt)
          },
          { note: 'Showing cached data while updating.' }
        );
      } catch (err) {
        console.warn('[usgs-iv] Failed to read cache', err);
      }
    }

    saveCache({ points, siteName, units }) {
      if (!hasStorage) return;
      try {
        const payload = {
          version: STORAGE_VERSION,
          savedAt: Date.now(),
          siteName,
          units,
          points: points.map((point) => [point.x.toISOString(), point.y])
        };
        window.localStorage.setItem(this.storageKey, JSON.stringify(payload));
      } catch (err) {
        console.warn('[usgs-iv] Failed to store cache', err);
      }
    }

    classifyHttpStatus(status) {
      if (status === 403 || status === 429) return 'rate-limit';
      if (status >= 500) return 'server';
      return 'http';
    }

    buildWarning(error) {
      if (!error) return 'Failed to load data.';
      if (error.kind === 'offline') {
        return 'Offline. Waiting for network connection.';
      }
      if (error.kind === 'timeout') {
        return 'USGS request timed out. Retrying.';
      }
      if (error.kind === 'rate-limit') {
        return 'USGS rate limit or access blocked (403/429). Reduce refresh interval or try later.';
      }
      if (error.kind === 'server') {
        return 'USGS service error. Retrying.';
      }
      if (error.kind === 'schema') {
        return error.message || 'Unexpected response format.';
      }
      if (error.kind === 'parse') {
        return 'Unexpected response format (JSON).';
      }
      if (error.kind === 'http') {
        return error.status
          ? `USGS request failed (${error.status}). Retrying.`
          : 'USGS request failed. Retrying.';
      }
      return error.message || 'Failed to load data.';
    }

    computeDelay(success, kind) {
      if (success) {
        this.failCount = 0;
        return this.applyJitter(this.config.refreshMs);
      }
      const bump = kind === 'rate-limit' ? 2 : 1;
      this.failCount = Math.min(this.failCount + bump, 6);
      const baseDelay = this.config.refreshMs * Math.pow(2, this.failCount);
      return this.applyJitter(Math.min(MAX_BACKOFF_MS, baseDelay));
    }

    applyJitter(delay) {
      const jitter = 0.9 + Math.random() * 0.2;
      return Math.max(1000, delay * jitter);
    }

    scheduleNext(success, kind) {
      if (this.timerId) {
        clearTimeout(this.timerId);
      }
      if (document.hidden) {
        return;
      }
      const delay = this.computeDelay(success, kind);
      this.timerId = setTimeout(() => this.requestRefresh('timer'), delay);
    }

    requestRefresh(reason) {
      if (this.inFlight) {
        this.pendingRefresh = true;
        return;
      }
      if (document.hidden) {
        return;
      }
      if (!navigator.onLine) {
        this.handleError(createError('offline', 'Offline'));
        return;
      }
      this.fetchAndRender(reason);
    }

    handleError(error) {
      const warning = this.buildWarning(error);
      const lastRefresh = this.lastSuccess ? this.lastSuccess.lastRefresh : null;
      const lastObs = this.lastSuccess ? this.lastSuccess.lastObs : null;
      this.setStatus({ lastRefresh, lastObs, warning });
      this.scheduleNext(false, error.kind);
    }

    abortInFlight() {
      if (this.abortController) {
        this.abortedForVisibility = true;
        this.abortController.abort();
      }
    }

    async fetchForecastPayload(signal) {
      if (this.config.mode !== 'discharge' || !this.config.forecastUrl) {
        return { payload: null, warning: null };
      }

      try {
        const response = await fetch(this.config.forecastUrl, {
          cache: 'no-store',
          signal
        });
        if (!response.ok) {
          return {
            payload: null,
            warning: `Forecast overlay unavailable (${response.status}).`
          };
        }
        const payload = await response.json();
        if (!payload || typeof payload !== 'object') {
          return { payload: null, warning: 'Forecast overlay unavailable (invalid JSON payload).' };
        }
        return { payload, warning: null };
      } catch (err) {
        if (err && err.name === 'AbortError') {
          throw err;
        }
        console.warn('[usgs-iv] forecast overlay fetch failed', err);
        return { payload: null, warning: 'Forecast overlay unavailable (fetch failed).' };
      }
    }

    /**
     * Fetch USGS data and render the Plotly chart.
     */
    async fetchAndRender(reason) {
      if (this.inFlight) return;
      this.inFlight = true;
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.config.timeoutMs);
      this.abortController = controller;

      try {
        const response = await fetch(buildUrl(this.config), {
          cache: 'no-store',
          signal: controller.signal
        });

        if (!response.ok) {
          const kind = this.classifyHttpStatus(response.status);
          throw createError(kind, `USGS request failed (${response.status})`, response.status);
        }

        let payload = null;
        try {
          payload = await response.json();
        } catch (err) {
          throw createError('parse', 'Unexpected response format (JSON).');
        }

        const { series, points } = extractSeries(payload);
        const siteName = series.sourceInfo && series.sourceInfo.siteName;
        const units = series.variable && series.variable.unit && series.variable.unit.unitCode;
        const lastObs = points[points.length - 1].x;
        const lastRefresh = new Date();
        const forecastResult = await this.fetchForecastPayload(controller.signal);

        this.renderPlot({
          points,
          siteName,
          units,
          lastObs,
          lastRefresh,
          forecastPayload: forecastResult.payload
        }, {
          note: forecastResult.warning || undefined
        });
        this.saveCache({ points, siteName, units });
        this.scheduleNext(true);
      } catch (err) {
        if (err && err.name === 'AbortError' && (this.abortedForVisibility || document.hidden)) {
          return;
        }
        const error = err && err.kind
          ? err
          : createError(err.name === 'AbortError' ? 'timeout' : 'http', err.message || 'Request failed');
        console.warn('[usgs-iv]', reason || 'fetch', error);
        this.handleError(error);
      } finally {
        clearTimeout(timeoutId);
        this.inFlight = false;
        this.abortController = null;
        this.abortedForVisibility = false;
        if (this.pendingRefresh) {
          this.pendingRefresh = false;
          this.requestRefresh('pending');
        }
      }
    }
  }

  /**
   * Initialize all plot instances on the page.
   */
  function initPlots() {
    const containers = document.querySelectorAll('.usgs-iv-plot');
    if (!containers.length) return;

    containers.forEach((container) => {
      const instance = new UsgsIvPlot(container);
      instances.push(instance);
      instance.init();
    });

    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        instances.forEach((instance) => {
          if (instance.timerId) {
            clearTimeout(instance.timerId);
            instance.timerId = null;
          }
          instance.abortInFlight();
        });
      } else {
        instances.forEach((instance) => instance.requestRefresh('visible'));
      }
    });

    window.addEventListener('online', () => {
      instances.forEach((instance) => instance.requestRefresh('online'));
    });

    window.addEventListener('offline', () => {
      instances.forEach((instance) => instance.handleError(createError('offline', 'Offline')));
    });

    window.addEventListener('gefs:timeline-window', () => {
      instances.forEach((instance) => instance.rerenderForTimeline());
    });

    let themeRerenderTimer = null;
    const scheduleThemeRerender = () => {
      if (themeRerenderTimer) {
        clearTimeout(themeRerenderTimer);
      }
      themeRerenderTimer = setTimeout(() => {
        themeRerenderTimer = null;
        instances.forEach((instance) => instance.rerenderForTheme());
      }, 90);
    };

    const themeToggles = document.querySelectorAll('[data-theme-toggle]');
    themeToggles.forEach((toggle) => {
      toggle.addEventListener('click', scheduleThemeRerender);
    });

    const themeObserver = new MutationObserver((records) => {
      for (let i = 0; i < records.length; i += 1) {
        const rec = records[i];
        if (rec.type === 'attributes' && rec.attributeName === 'class') {
          scheduleThemeRerender();
          break;
        }
      }
    });
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    if (document.body) {
      themeObserver.observe(document.body, { attributes: true, attributeFilter: ['class'] });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPlots);
  } else {
    initPlots();
  }
})();
