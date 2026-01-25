(() => {
  'use strict';

  if (window.__usgsIvPlotInitialized) {
    return;
  }
  window.__usgsIvPlotInitialized = true;

  const DEFAULTS = {
    period: 'P30D',
    refreshMin: 15,
    timeoutSec: 20,
    yMin: 0,
    yMax: 12
  };
  const ENDPOINT_BASE = 'https://waterservices.usgs.gov/nwis/iv/';
  const MAX_BACKOFF_MS = 60 * 60 * 1000;
  const MIN_CACHE_AGE_MS = 30 * 60 * 1000;
  const STORAGE_VERSION = 2;

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

  function getThemeColors() {
    const styles = getComputedStyle(document.documentElement);
    return {
      text: styles.getPropertyValue('--text-color').trim() || '#1f2933',
      grid: styles.getPropertyValue('--border-color').trim() || '#e2e8f0',
      line: styles.getPropertyValue('--accent-color').trim() || '#1b63c6'
    };
  }

  function createError(kind, message, status) {
    const error = new Error(message);
    error.kind = kind;
    if (status) error.status = status;
    return error;
  }

  function transformValue(value) {
    const safe = Math.max(0, value);
    if (Math.log1p) return Math.log1p(safe);
    return Math.log(safe + 1);
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
          y: transformValue(numeric)
        };
      })
      .filter(Boolean)
      .sort((a, b) => a.x - b.x);

    if (!points.length) {
      throw createError('schema', 'No numeric discharge values available.');
    }

    return { series, points };
  }

  function buildLayout(yTitle, colors, yRange, shapes) {
    return {
      margin: { l: 60, r: 20, t: 20, b: 50 },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      shapes: shapes || [],
      font: {
        color: colors.text,
        family: 'Source Sans Pro, Helvetica, Arial, sans-serif'
      },
      xaxis: {
        title: 'Date',
        type: 'date',
        gridcolor: colors.grid,
        zerolinecolor: colors.grid,
        tickformat: '%b %d'
      },
      yaxis: {
        title: yTitle,
        gridcolor: colors.grid,
        zerolinecolor: colors.grid,
        range: yRange,
        autorange: false
      }
    };
  }

  function buildTrace(points, units, colors) {
    const unitLabel = units ? ` ${units}` : '';
    return {
      x: points.map((p) => p.x),
      y: points.map((p) => p.y),
      type: 'scatter',
      mode: 'lines',
      line: { color: colors.line, width: 2 },
      hovertemplate: `%{x}<br>%{y:.2f}${unitLabel}<extra></extra>`
    };
  }

  function buildThresholdShapes(config, colors) {
    const shapes = [];
    const minor = config.thresholdMinor;
    const major = config.thresholdMajor;
    const yMin = config.yMin;
    const yMax = config.yMax;

    if (!Number.isFinite(minor) || !Number.isFinite(major)) {
      return shapes;
    }

    const minorTransformed = transformValue(minor);
    const majorTransformed = transformValue(major);

    if (majorTransformed <= minorTransformed) {
      console.warn('[usgs-iv] Major threshold must exceed minor threshold.', config);
      return shapes;
    }

    const minorColor = 'rgba(242, 201, 76, 0.18)';
    const majorColor = 'rgba(220, 38, 38, 0.16)';
    const minorLine = colors && colors.line ? colors.line : '#f2c94c';
    const majorLine = '#dc2626';

    const minorLower = Math.max(yMin, minorTransformed);
    const minorUpper = Math.min(yMax, majorTransformed);
    if (minorUpper > minorLower) {
      shapes.push({
        type: 'rect',
        xref: 'paper',
        yref: 'y',
        x0: 0,
        x1: 1,
        y0: minorLower,
        y1: minorUpper,
        fillcolor: minorColor,
        line: { width: 0 },
        layer: 'below'
      });
    }

    const majorLower = Math.max(yMin, majorTransformed);
    const majorUpper = yMax;
    if (majorUpper > majorLower) {
      shapes.push({
        type: 'rect',
        xref: 'paper',
        yref: 'y',
        x0: 0,
        x1: 1,
        y0: majorLower,
        y1: majorUpper,
        fillcolor: majorColor,
        line: { width: 0 },
        layer: 'below'
      });
    }

    shapes.push({
      type: 'line',
      xref: 'paper',
      x0: 0,
      x1: 1,
      yref: 'y',
      y0: minorTransformed,
      y1: minorTransformed,
      line: { color: minorLine, width: 1.5, dash: 'dash' }
    });

    shapes.push({
      type: 'line',
      xref: 'paper',
      x0: 0,
      x1: 1,
      yref: 'y',
      y0: majorTransformed,
      y1: majorTransformed,
      line: { color: majorLine, width: 1.5, dash: 'dash' }
    });

    return shapes;
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

      this.storageKey = this.buildStorageKey();
    }

    readConfig(container) {
      const dataset = container.dataset || {};
      const refreshMin = parseNumber(dataset.refreshMin, DEFAULTS.refreshMin);
      const timeoutSec = parseNumber(dataset.timeoutSec, DEFAULTS.timeoutSec);
      const yMin = parseNumber(dataset.yMin, DEFAULTS.yMin);
      const yMax = parseNumber(dataset.yMax, DEFAULTS.yMax);
      return {
        siteId: dataset.site,
        parameterCd: dataset.parameter,
        period: dataset.period || DEFAULTS.period,
        refreshMs: clampNumber(refreshMin, 1, 1440, DEFAULTS.refreshMin) * 60 * 1000,
        timeoutMs: clampNumber(timeoutSec, 5, 60, DEFAULTS.timeoutSec) * 1000,
        title: dataset.title || '',
        yLabel: dataset.ylabel || 'Discharge',
        yMin: yMin,
        yMax: yMax,
        thresholdMinor: parseOptionalNumber(dataset.thresholdMinor),
        thresholdMajor: parseOptionalNumber(dataset.thresholdMajor)
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

      if (this.config.yMax <= this.config.yMin) {
        console.warn('[usgs-iv] data-y-max must exceed data-y-min.', this.container);
      }

      if (this.config.thresholdMinor && this.config.thresholdMajor &&
          this.config.thresholdMajor <= this.config.thresholdMinor) {
        console.warn('[usgs-iv] data-threshold-major should exceed data-threshold-minor.', this.container);
      }
      if (this.config.thresholdMajor) {
        const majorTransformed = transformValue(this.config.thresholdMajor);
        if (majorTransformed >= this.config.yMax) {
          console.warn('[usgs-iv] data-y-max should exceed the transformed major threshold.', this.container);
        }
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
      const parts = [];

      const siteValue = siteName || data.siteName;
      const unitsValue = units || data.units;
      const lastObsValue = lastObs || data.lastObs;
      const lastRefreshValue = lastRefresh || data.lastRefresh;

      if (siteValue) parts.push(`Site: ${siteValue}`);
      if (unitsValue) parts.push(`Units: ${unitsValue}`);
      if (lastObsValue) parts.push(`Last obs: ${formatDate(lastObsValue)}`);
      if (lastRefreshValue) parts.push(`Last refresh: ${formatDate(lastRefreshValue)}`);
      if (note) parts.push(`Note: ${note}`);
      if (warning) parts.push(`Warning: ${warning}`);
      if (!parts.length) parts.push('Loading data...');

      this.statusEl.textContent = parts.join(' | ');
      if (warning) {
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

    renderPlot({ points, siteName, units, lastObs, lastRefresh }, options = {}) {
      if (!window.Plotly) {
        this.setStatus({ warning: 'Plotly failed to load.' });
        return;
      }

      const colors = getThemeColors();
      const displayUnits = 'log1';
      const yTitleBase = `log1p(${this.config.yLabel})`;
      const yTitle = `${yTitleBase} (${displayUnits})`;
      const shapes = buildThresholdShapes(this.config, colors);
      const yRange = [this.config.yMin, this.config.yMax];

      Plotly.react(
        this.chartEl,
        [buildTrace(points, displayUnits, colors)],
        buildLayout(yTitle, colors, yRange, shapes),
        { responsive: true, displayModeBar: false }
      );

      this.lastSuccess = {
        siteName,
        units: displayUnits,
        lastObs,
        lastRefresh
      };

      this.updateAriaLabel(siteName);
      this.setLoadedState(true);
      if (!options.silentStatus) {
        this.setStatus({ siteName, units, lastObs, lastRefresh, note: options.note });
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
        return `USGS request failed (${error.status}). Retrying.`;
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

    /**
     * Fetch USGS data and render the Plotly chart.
     */
    async fetchAndRender(reason) {
      if (this.inFlight) return;
      this.inFlight = true;
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.config.timeoutMs);
      let response = null;
      this.abortController = controller;

      try {
        response = await fetch(buildUrl(this.config), {
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

        this.renderPlot({ points, siteName, units, lastObs, lastRefresh });
        this.saveCache({ points, siteName, units: displayUnits });
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
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPlots);
  } else {
    initPlots();
  }
})();
