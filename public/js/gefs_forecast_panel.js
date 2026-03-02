(() => {
  'use strict';

  if (window.__gefsForecastPanelInitialized) return;
  window.__gefsForecastPanelInitialized = true;
  const PLOT_LAYOUT_STYLE = {
    margin: { l: 60, r: 20, t: 24, b: 52 },
    legend: {
      orientation: 'h',
      y: 1.18,
      x: 0,
      xanchor: 'left',
      fontSize: 11
    }
  };
  const FORECAST_START_MARKER_STYLE = {
    color: '#111827',
    width: 1.4,
    dash: 'dash',
    label: 'Forecast start'
  };

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
      const ts = parseDate(point.t);
      const value = numberOrNull(point.v);
      if (!ts || value === null) return;
      x.push(ts);
      y.push(value);
    });
    return { x, y };
  }

  function hasSeries(points) {
    return Array.isArray(points) && points.length > 0;
  }

  function pickCycleMarker(points, initDate, requireAfterInit) {
    if (!Array.isArray(points) || !initDate) return null;
    const parsed = points
      .map((point) => {
        if (!point || !point.t) return null;
        const ts = parseDate(point.t);
        const value = numberOrNull(point.v);
        if (!ts || value === null) return null;
        return { ts, value };
      })
      .filter(Boolean)
      .sort((a, b) => a.ts - b.ts);
    if (!parsed.length) return null;

    if (requireAfterInit) {
      const firstAfter = parsed.find((row) => row.ts > initDate);
      if (firstAfter) return { t: firstAfter.ts.toISOString(), v: firstAfter.value };
    }

    const firstAtOrAfter = parsed.find((row) => row.ts >= initDate);
    if (firstAtOrAfter) return { t: firstAtOrAfter.ts.toISOString(), v: firstAtOrAfter.value };
    return { t: parsed[0].ts.toISOString(), v: parsed[0].value };
  }

  function deriveAnalysisContextFromPayload(payload) {
    if (!payload || typeof payload !== 'object') return {};
    const initDate = parseDate(payload.init_time_utc);
    if (!initDate) return {};

    const windowDays = Math.max(1, numberOrNull(payload.observation_window_days) || 20);
    const startDate = new Date(initDate.getTime() - windowDays * 24 * 3600 * 1000);
    const derived = {
      window_days: windowDays,
      start_utc: startDate.toISOString(),
      end_utc: initDate.toISOString(),
      precip_proxy_valid_offset_hours: 3,
      precip_f003_proxy: {},
      soil_f000: {}
    };

    const precipLevels = payload.precip && typeof payload.precip === 'object' ? payload.precip : {};
    Object.keys(precipLevels).forEach((level) => {
      const marker = pickCycleMarker((precipLevels[level] || {}).p50, initDate, true);
      if (marker) derived.precip_f003_proxy[level] = [marker];
    });

    const soilLevels = payload.soil_moisture && typeof payload.soil_moisture === 'object'
      ? payload.soil_moisture
      : {};
    Object.keys(soilLevels).forEach((level) => {
      const marker = pickCycleMarker((soilLevels[level] || {}).p50, initDate, false);
      if (marker) derived.soil_f000[level] = [marker];
    });

    return derived;
  }

  function scaleSeries(points, factor) {
    if (!Array.isArray(points)) return [];
    if (!Number.isFinite(factor)) return [];
    const out = [];
    points.forEach((point) => {
      if (!point || !point.t) return;
      const value = numberOrNull(point.v);
      if (value === null) return;
      out.push({ t: point.t, v: value * factor });
    });
    return out;
  }

  function seriesMaxAbs(points) {
    if (!Array.isArray(points) || !points.length) return null;
    let maxAbs = null;
    points.forEach((point) => {
      const value = numberOrNull(point && point.v);
      if (value === null) return;
      const absValue = Math.abs(value);
      if (maxAbs === null || absValue > maxAbs) maxAbs = absValue;
    });
    return maxAbs;
  }

  function normalizeUnitLabel(unitRaw) {
    return String(unitRaw || '')
      .trim()
      .toLowerCase()
      .replace(/\*\*/g, '^')
      .replace(/\s+/g, ' ');
  }

  function resolvePrecipFactorToMm(unitRaw, warnings, sourceLabel) {
    const unit = normalizeUnitLabel(unitRaw);
    const compact = unit.replace(/\s+/g, '');

    if (!unit) {
      warnings.push(`${sourceLabel}: missing precip units, assuming mm water-equivalent`);
      return 1;
    }

    if (compact === 'mm' || unit.includes('millimeter') || unit.includes('millimetre')) return 1;
    if (compact === 'cm' || unit.includes('centimeter') || unit.includes('centimetre')) return 10;
    if (compact === 'm' || unit === 'meter' || unit === 'metre') return 1000;
    if (compact === 'in' || compact === 'inch' || compact === 'inches' || unit.includes('inch')) return 25.4;
    if (
      compact.includes('kg/m2') ||
      compact.includes('kg/m^2') ||
      compact.includes('kgm-2') ||
      compact.includes('kgm^-2')
    ) {
      return 1;
    }

    warnings.push(`${sourceLabel}: unrecognized precip units "${unitRaw || 'unknown'}", hiding series`);
    return null;
  }

  function resolveSoilFactorToFraction(unitRaw, samplePoints, warnings, sourceLabel) {
    const unit = normalizeUnitLabel(unitRaw);
    const compact = unit.replace(/\s+/g, '');

    if (
      compact.includes('proportion') ||
      compact.includes('fraction') ||
      compact.includes('m3/m3') ||
      compact.includes('m^3/m^3') ||
      compact.includes('m3m-3') ||
      compact.includes('m^3m^-3')
    ) {
      return 1;
    }
    if (compact.includes('%') || compact.includes('percent')) return 0.01;

    const maxAbs = seriesMaxAbs(samplePoints);
    if (maxAbs === null) return 1;
    if (maxAbs <= 1.5) return 1;
    if (maxAbs <= 100) {
      warnings.push(`${sourceLabel}: inferred percent units and converted to fraction`);
      return 0.01;
    }

    warnings.push(`${sourceLabel}: incompatible values for fraction units, hiding series`);
    return null;
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
    const fallbackEnd = new Date(initDate.getTime() + 48 * 3600 * 1000);
    const end = latest && latest > initDate ? latest : fallbackEnd;
    return [start, end];
  }

  function collectForecastPointGroups(payload) {
    const pointGroups = [];
    if (!payload || typeof payload !== 'object') return pointGroups;

    const collectBlock = (block) => {
      if (!block || typeof block !== 'object') return;
      ['p10', 'p50', 'p90', 'mean'].forEach((key) => {
        if (Array.isArray(block[key])) pointGroups.push(block[key]);
      });
    };

    const precipLevels = payload.precip && typeof payload.precip === 'object' ? payload.precip : {};
    Object.values(precipLevels).forEach((levelBlock) => collectBlock(levelBlock));

    const soilLevels = payload.soil_moisture && typeof payload.soil_moisture === 'object'
      ? payload.soil_moisture
      : {};
    Object.values(soilLevels).forEach((levelBlock) => collectBlock(levelBlock));
    return pointGroups;
  }

  function computeForecastHorizonHours(payload, initDate) {
    if (!payload || !initDate) return null;
    const forecastEnd = latestPointDate(collectForecastPointGroups(payload));
    if (!forecastEnd || forecastEnd <= initDate) return null;
    const hours = (forecastEnd.getTime() - initDate.getTime()) / (1000 * 3600);
    return Number.isFinite(hours) && hours >= 0 ? hours : null;
  }

  function publishTimelineWindow(payload, observationWindowDays) {
    const initDate = parseDate(payload && payload.init_time_utc);
    if (!initDate) return;

    const horizonHours = computeForecastHorizonHours(payload, initDate);
    if (!Number.isFinite(horizonHours)) return;

    const normalizedWindowDays = Math.max(1, numberOrNull(observationWindowDays) || 20);
    const detail = {
      source: 'gefs-forecast-panel',
      initTimeUtc: initDate.toISOString(),
      observationWindowDays: normalizedWindowDays,
      forecastHorizonHours: horizonHours,
      publishedAtUtc: new Date().toISOString()
    };

    const prior = window.__gefsTimelineWindow && typeof window.__gefsTimelineWindow === 'object'
      ? window.__gefsTimelineWindow
      : null;
    const sameWindow = prior
      && prior.initTimeUtc === detail.initTimeUtc
      && Number(prior.observationWindowDays) === detail.observationWindowDays
      && Math.abs(Number(prior.forecastHorizonHours) - detail.forecastHorizonHours) < 0.05;
    if (sameWindow) return;

    window.__gefsTimelineWindow = detail;
    if (typeof window.CustomEvent === 'function') {
      window.dispatchEvent(new CustomEvent('gefs:timeline-window', { detail }));
    }
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
        size: opts.markerSize || 4.8,
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
      accent: styles.getPropertyValue('--accent-color').trim() || '#1d4ed8',
      muted: styles.getPropertyValue('--text-subtle').trim() || '#64748b',
      surface: styles.getPropertyValue('--surface-1').trim() || '#ffffff'
    };
  }

  function buildForecastStartMarker(initTime) {
    if (!initTime) return { shapes: [], annotations: [] };
    return {
      shapes: [
        {
          type: 'line',
          xref: 'x',
          yref: 'paper',
          x0: initTime,
          x1: initTime,
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
          x: initTime,
          yref: 'paper',
          y: 1,
          text: FORECAST_START_MARKER_STYLE.label,
          showarrow: false,
          font: { size: 11, color: FORECAST_START_MARKER_STYLE.color },
          xanchor: 'left',
          yanchor: 'bottom',
          bgcolor: 'rgba(255, 255, 255, 0.6)',
          bordercolor: 'rgba(255, 255, 255, 0.0)',
          borderpad: 2
        }
      ]
    };
  }

  function layout(yTitle, colors, options) {
    const opts = options || {};
    const chartLayout = {
      margin: PLOT_LAYOUT_STYLE.margin,
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
        title: 'Date (UTC)',
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
        zeroline: opts.showZeroLine === undefined ? true : Boolean(opts.showZeroLine),
        zerolinecolor: colors.grid,
        showline: true,
        linecolor: colors.grid,
        automargin: true,
        rangemode: opts.yRangeMode || 'normal'
      },
      legend: {
        orientation: PLOT_LAYOUT_STYLE.legend.orientation,
        y: opts.legendY === undefined ? PLOT_LAYOUT_STYLE.legend.y : opts.legendY,
        x: PLOT_LAYOUT_STYLE.legend.x,
        xanchor: PLOT_LAYOUT_STYLE.legend.xanchor,
        font: { size: PLOT_LAYOUT_STYLE.legend.fontSize, color: colors.text },
        itemclick: 'toggle',
        itemdoubleclick: 'toggleothers'
      }
    };

    if (Array.isArray(opts.xRange) && opts.xRange.length === 2) {
      chartLayout.xaxis.range = opts.xRange;
    }
    if (opts.yTickFormat) {
      chartLayout.yaxis.tickformat = opts.yTickFormat;
    }
    if (opts.initTime) {
      const marker = buildForecastStartMarker(opts.initTime);
      chartLayout.shapes = marker.shapes;
      chartLayout.annotations = marker.annotations;
    }

    return chartLayout;
  }

  function levelSortKey(level) {
    const match = String(level).match(/^([0-9.]+)\s*-/);
    return match ? Number(match[1]) : 999;
  }

  function estimateForecastHorizonText(payload) {
    if (!payload || typeof payload !== 'object') return 'forecast ahead';
    const initDate = parseDate(payload.init_time_utc);
    if (!initDate) return 'forecast ahead';

    const horizonHours = computeForecastHorizonHours(payload, initDate);
    if (!Number.isFinite(horizonHours) || horizonHours <= 0) return 'forecast ahead';
    if (horizonHours < 24) return `about ${Math.round(horizonHours)} hours ahead`;
    return `about ${Math.round(horizonHours / 24)} days ahead`;
  }

  function summarizeStatusWarnings(warnings) {
    const cleaned = Array.isArray(warnings)
      ? Array.from(new Set(warnings.filter((msg) => typeof msg === 'string' && msg.trim().length > 0)))
      : [];
    if (!cleaned.length) return [];

    const out = [];
    let hasSeriesIssue = false;
    cleaned.forEach((msg) => {
      if (msg.startsWith('Update appears delayed')) {
        out.push(msg);
      } else {
        hasSeriesIssue = true;
      }
    });
    if (hasSeriesIssue) {
      out.push('Some lines are temporarily unavailable while data refreshes.');
    }
    return out;
  }

  function setStatus(el, payload, warnings) {
    if (!el) return;

    const generated = payload ? formatDate(payload.generated_at_utc) : '--';
    const initTime = payload ? formatDate(payload.init_time_utc) : '--';
    const members = payload && Number.isFinite(Number(payload.member_count))
      ? Number(payload.member_count)
      : '--';

    const retroWindowDays = payload && Number.isFinite(Number(payload.observation_window_days))
      ? Number(payload.observation_window_days)
      : null;
    const horizonText = estimateForecastHorizonText(payload);
    const warningParts = summarizeStatusWarnings(warnings);
    const missingLayers = payload && Array.isArray(payload.missing_levels) ? payload.missing_levels : [];
    const layerText = missingLayers.length ? 'Some soil depth layers are currently unavailable.' : '';
    const coverageText = retroWindowDays
      ? `Coverage: last ${retroWindowDays} days + ${horizonText}`
      : `Coverage: ${horizonText}`;
    const warningText = warningParts.length ? ` | ${warningParts.join(' | ')}` : '';
    const layerWarningText = layerText ? ` | ${layerText}` : '';

    el.textContent = `Updated: ${generated} | Forecast start: ${initTime} | Ensemble members: ${members} | ${coverageText}${layerWarningText}${warningText}`;
    el.classList.toggle('plot-status--error', warningParts.length > 0);
  }

  function buildFetchUrl(baseUrl) {
    const url = new URL(baseUrl, window.location.origin);
    url.searchParams.set('_ts', String(Date.now()));
    return url.toString();
  }

  function renderPrecipChart(precipEl, payload, initDate, observationWindowDays, colors, statusWarnings) {
    const precipLevels = payload.precip || {};
    const precipLevelName = precipLevels.surface ? 'surface' : Object.keys(precipLevels)[0];
    const precipLevel = precipLevelName ? precipLevels[precipLevelName] : null;

    if (!precipLevel || typeof precipLevel !== 'object') {
      Plotly.purge(precipEl);
      statusWarnings.push('Precipitation data is temporarily unavailable.');
      return;
    }

    const precipFactor = resolvePrecipFactorToMm(
      precipLevel.units || '',
      statusWarnings,
      'GEFS precipitation'
    );
    if (precipFactor === null) {
      Plotly.purge(precipEl);
      return;
    }

    const forecast = {
      p10: scaleSeries(precipLevel.p10, precipFactor),
      p50: scaleSeries(precipLevel.p50, precipFactor),
      p90: scaleSeries(precipLevel.p90, precipFactor),
      mean: scaleSeries(precipLevel.mean, precipFactor)
    };

    const retrospective = payload.retrospective || {};
    const retroRaw = ((retrospective.precip || {})[precipLevelName]) || null;
    const retro = retroRaw
      ? {
        p10: scaleSeries(retroRaw.p10, precipFactor),
        p50: scaleSeries(retroRaw.p50, precipFactor),
        p90: scaleSeries(retroRaw.p90, precipFactor),
        mean: scaleSeries(retroRaw.mean, precipFactor)
      }
      : null;

    const analysisContext = payload.gefs_analysis_context || {};
    const analysis = scaleSeries(((analysisContext.precip_f003_proxy || {})[precipLevelName]) || [], precipFactor);

    const traces = [];

    if (retro && (hasSeries(retro.p10) || hasSeries(retro.p50) || hasSeries(retro.p90))) {
      const retroBand = buildBandTrace(
        retro.p10,
        retro.p90,
        'Recent range (10-90%)',
        'rgba(100,116,139,0.18)',
        { showLegend: true, legendGroup: 'precip_retro' }
      );
      if (retroBand) traces.push(retroBand);

      const retroP50 = buildLineTrace(
        retro.p50,
        'Recent median',
        '#475569',
        'dot',
        {
          width: 1.5,
          unit: 'mm',
          valueFormat: '.2f',
          hoverLabel: 'Recent median',
          legendGroup: 'precip_retro'
        }
      );
      if (retroP50) traces.push(retroP50);
    }

    if (hasSeries(analysis)) {
      const analysisTrace = buildLineTrace(
        analysis,
        'Recent cycle values',
        '#334155',
        'dot',
        {
          width: 1.8,
          opacity: 0.92,
          mode: analysis.length <= 6 ? 'markers+lines' : 'lines+markers',
          markerSize: 6.8,
          markerSymbol: 'diamond',
          unit: 'mm',
          valueFormat: '.2f',
          hoverLabel: 'Recent cycle values',
          legendGroup: 'precip_analysis'
        }
      );
      if (analysisTrace) traces.push(analysisTrace);
    }

    const band = buildBandTrace(
      forecast.p10,
      forecast.p90,
      'Forecast range (10-90%)',
      'rgba(30,64,175,0.17)',
      { showLegend: true, legendGroup: 'precip_forecast' }
    );
    if (band) traces.push(band);

    const meanTrace = buildLineTrace(
      forecast.mean,
      'Forecast average',
      '#ea580c',
      'dash',
      {
        width: 1.85,
        unit: 'mm',
        valueFormat: '.2f',
        hoverLabel: 'Forecast average',
        legendGroup: 'precip_forecast'
      }
    );
    if (meanTrace) traces.push(meanTrace);

    const p50Trace = buildLineTrace(
      forecast.p50,
      'Forecast median',
      '#1d4ed8',
      'solid',
      {
        width: 2.6,
        unit: 'mm',
        valueFormat: '.2f',
        hoverLabel: 'Forecast median',
        legendGroup: 'precip_forecast'
      }
    );
    if (p50Trace) traces.push(p50Trace);

    if (!traces.length) {
      Plotly.purge(precipEl);
      statusWarnings.push('Precipitation lines are temporarily unavailable.');
      return;
    }

    const xRange = buildXRange(
      initDate,
      observationWindowDays,
      [analysis, forecast.p10, forecast.p50, forecast.p90, forecast.mean, retro && retro.p10, retro && retro.p50, retro && retro.p90]
    );

    Plotly.react(
      precipEl,
      traces,
      layout('Precipitation (mm)', colors, {
        xRange,
        initTime: initDate,
        yTickFormat: '.1f',
        yRangeMode: 'tozero',
        showZeroLine: true
      }),
      { responsive: true, displayModeBar: false }
    );
  }

  function renderSoilChart(soilEl, payload, initDate, observationWindowDays, colors, statusWarnings) {
    const levels = Object.keys(payload.soil_moisture || {}).sort((a, b) => levelSortKey(a) - levelSortKey(b));
    if (!levels.length) {
      Plotly.purge(soilEl);
      statusWarnings.push('Soil moisture data is temporarily unavailable.');
      return;
    }

    const palette = ['#1d4ed8', '#0284c7', '#16a34a', '#f59e0b'];
    const traces = [];
    const pointGroups = [];
    const analysisSoilBlock = (payload.gefs_analysis_context || {}).soil_f000 || {};
    const retrospective = payload.retrospective || {};

    levels.forEach((level, idx) => {
      const block = payload.soil_moisture[level];
      if (!block || typeof block !== 'object') return;
      const levelColor = palette[idx % palette.length];

      const factor = resolveSoilFactorToFraction(
        block.units || '',
        block.p50,
        statusWarnings,
        `GEFS SOILW ${level}`
      );
      if (factor === null) return;

      const forecast = {
        p10: scaleSeries(block.p10, factor),
        p50: scaleSeries(block.p50, factor),
        p90: scaleSeries(block.p90, factor)
      };

      const analysis = scaleSeries((analysisSoilBlock[level]) || [], factor);
      if (hasSeries(analysis)) {
        const analysisTrace = buildLineTrace(
          analysis,
          idx === 0 ? 'Recent cycle values' : `Recent cycle · ${level}`,
          levelColor,
          'dot',
          {
            width: 1.25,
            opacity: 0.9,
            mode: analysis.length <= 6 ? 'markers+lines' : 'lines+markers',
            markerSize: 5.6,
            markerSymbol: 'circle',
            showlegend: idx === 0,
            unit: 'm3/m3',
            valueFormat: '.3f',
            hoverLabel: `Recent cycle · ${level}`,
            legendGroup: 'soil_analysis'
          }
        );
        if (analysisTrace) traces.push(analysisTrace);
      }

      const retroRaw = ((retrospective.soil_moisture || {})[level]) || null;
      const retro = retroRaw ? scaleSeries(retroRaw.p50, factor) : [];
      if (hasSeries(retro)) {
        const retroTrace = buildLineTrace(
          retro,
          idx === 0 ? 'Recent median' : `Recent median · ${level}`,
          '#64748b',
          'dot',
          {
            width: 1.35,
            opacity: 0.7,
            showlegend: idx === 0,
            unit: 'm3/m3',
            valueFormat: '.3f',
            hoverLabel: `Recent median · ${level}`,
            legendGroup: 'soil_retro'
          }
        );
        if (retroTrace) traces.push(retroTrace);
      }

      const band = buildBandTrace(
        forecast.p10,
        forecast.p90,
        `${level} p10-p90`,
        `rgba(14,165,233,${0.07 + idx * 0.02})`,
        { showLegend: false, legendGroup: `soil_forecast_${idx}` }
      );
      if (band) traces.push(band);

      const soilP50 = buildLineTrace(
        forecast.p50,
        `Forecast median · ${level}`,
        levelColor,
        'solid',
        {
          width: 2.05,
          unit: 'm3/m3',
          valueFormat: '.3f',
          hoverLabel: `Forecast median · ${level}`,
          legendGroup: `soil_forecast_${idx}`
        }
      );
      if (soilP50) traces.push(soilP50);

      pointGroups.push(analysis, retro, forecast.p10, forecast.p50, forecast.p90);
    });

    if (!traces.length) {
      Plotly.purge(soilEl);
      statusWarnings.push('Soil moisture lines are temporarily unavailable.');
      return;
    }

    const xRange = buildXRange(initDate, observationWindowDays, pointGroups);
    Plotly.react(
      soilEl,
      traces,
      layout('Soil moisture (m3/m3)', colors, {
        xRange,
        initTime: initDate,
        yTickFormat: '.2f',
        showZeroLine: false
      }),
      { responsive: true, displayModeBar: false }
    );
  }

  function renderPanel(container, payload) {
    const precipEl = container.querySelector('.gefs-forecast-precip');
    const soilEl = container.querySelector('.gefs-forecast-soil');
    const statusEl = container.querySelector('.gefs-forecast-status');

    const colors = getThemeColors();
    const initDate = parseDate(payload.init_time_utc);
    const observationWindowDays = Math.max(
      1,
      numberOrNull(container.dataset.observationWindowDays) || numberOrNull(payload.observation_window_days) || 20
    );

    if (!payload.gefs_analysis_context || typeof payload.gefs_analysis_context !== 'object') {
      payload.gefs_analysis_context = deriveAnalysisContextFromPayload(payload);
    }

    publishTimelineWindow(payload, observationWindowDays);

    const statusWarnings = [];
    const staleHours = numberOrNull(container.dataset.staleHours) ?? numberOrNull(payload.stale_after_hours) ?? 12;
    const generatedDate = parseDate(payload.generated_at_utc);
    if (generatedDate) {
      const ageHours = (Date.now() - generatedDate.getTime()) / (1000 * 3600);
      if (ageHours > staleHours) statusWarnings.push(`Update appears delayed (${ageHours.toFixed(1)} hours old).`);
    }

    if (precipEl) renderPrecipChart(precipEl, payload, initDate, observationWindowDays, colors, statusWarnings);
    if (soilEl) renderSoilChart(soilEl, payload, initDate, observationWindowDays, colors, statusWarnings);

    setStatus(statusEl, payload, statusWarnings);
  }

  async function initOne(container) {
    if (!window.Plotly) return;

    const statusEl = container.querySelector('.gefs-forecast-status');
    const url = container.dataset.gefsUrl || '/assets/data/forecasts/gefs_big_trees_latest.json';
    const refreshMinutes = Math.max(1, numberOrNull(container.dataset.refreshMin) || 60);
    const refreshMs = refreshMinutes * 60 * 1000;
    let inFlight = false;
    let lastPayload = null;
    let rerenderTimer = null;

    function rerenderFromCache() {
      if (!lastPayload || typeof lastPayload !== 'object') return;
      try {
        renderPanel(container, lastPayload);
      } catch (err) {
        // Keep theme toggles resilient; next refresh will recover if needed.
      }
    }

    function scheduleThemeRerender() {
      if (!lastPayload || typeof lastPayload !== 'object') return;
      if (rerenderTimer) window.clearTimeout(rerenderTimer);
      rerenderTimer = window.setTimeout(() => {
        rerenderTimer = null;
        rerenderFromCache();
      }, 90);
    }

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

    async function refreshOnce() {
      if (inFlight) return;
      inFlight = true;
      try {
        const response = await fetch(buildFetchUrl(url), { cache: 'no-store' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        if (!payload || typeof payload !== 'object') throw new Error('Invalid JSON payload');
        lastPayload = payload;
        renderPanel(container, payload);
      } catch (err) {
        if (statusEl) {
          statusEl.textContent = 'Forecast data is temporarily unavailable. Please check back soon.';
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
