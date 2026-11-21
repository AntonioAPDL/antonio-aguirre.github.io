'use strict';

function makeDemoData(scenario = 'extreme') {
  const init = new Date();
  init.setUTCHours(0, 0, 0, 0);
  const day = 86400000;
  const stamp = (offset) => new Date(init.getTime() + offset * day).toISOString();
  const series = (values, start = 1) => values.map((v, i) => ({ t: stamp(start + i), v }));
  const flat = scenario === 'constant';
  const quiet = scenario === 'quiet';
  const missing = scenario === 'missing';
  const flowValues = flat ? [0, 0, 0] : quiet ? [12, 18, 24] : [0, 20, 100000];
  const observedValues = scenario === 'observed-peak' ? [10, 100000, 12] : [10, 12, 14];
  const usgs = {
    value: {
      timeSeries: [{
        sourceInfo: { siteName: 'SAN LORENZO R A BIG TREES CA' },
        variable: { unit: { unitCode: 'ft3/s' } },
        values: [{ value: Array.from({ length: 288 }, (_, i) => ({
          dateTime: new Date(init.getTime() - (288 - i) * 900000).toISOString(),
          value: String(flat ? 0 : observedValues[Math.floor(i / 96)])
        })) }]
      }]
    }
  };
  const flow = {
    generated_at_utc: init.toISOString(),
    units: ['ft3/s'],
    ranges: {
      short: { deterministic: series(flat ? [0, 0] : [15, 20]) },
      medium_range: {
        p10: series(flowValues.map((value) => value * 0.5)),
        p50: series(flowValues.map((value) => value * 0.75)),
        p90: series(flowValues)
      },
      long_range: missing ? {} : {
        p10: series(flat ? [0, 0] : [8, 10], 4),
        p50: series(flat ? [0, 0] : [18, 20], 4),
        p90: series(flat ? [0, 0] : [25, 30], 4)
      }
    }
  };
  const precipValues = flat ? [0, 0, 0] : quiet ? [0.01, 0.02, 0.03] : [1, 500, 3];
  const gefs = {
    generated_at_utc: init.toISOString(),
    init_time_utc: init.toISOString(),
    observation_window_days: 20,
    member_count: 31,
    precip: { surface: {
      units: 'mm', time_support: '24-hour total',
      p10: series(precipValues.map((value) => value * 0.1)),
      p50: series(precipValues.map((value) => value * 0.5)),
      p90: series(precipValues),
      mean: series(precipValues.map((value) => value * 0.6))
    } },
    soil_moisture: {},
    observed_retrospective: {
      daily_avg_ppt: series(flat ? [0, 0, 0] : [0, 70, 1], -3),
      daily_avg_soil_ERA5: series(flat ? [0.25, 0.25, 0.25] : [0.01, 0.2, 0.3], -3),
      daily_avg_soil_NWM_SOIL_W: series(flat ? [0.25, 0.25, 0.25] : [0.08, 0.15, 0.22], -3)
    }
  };
  ['0-0.1 m', '0.1-0.4 m', '0.4-1 m', '1-2 m'].forEach((level, i) => {
    gefs.soil_moisture[level] = {
      units: 'm3/m3', time_support: '24-hour mean',
      p10: series(flat ? [0.25, 0.25] : [0.1 + i * 0.03, 0.15 + i * 0.03]),
      p50: series(flat ? [0.25, 0.25] : [0.2 + i * 0.03, 0.25 + i * 0.03]),
      p90: series(flat ? [0.25, 0.25] : [0.4 + i * 0.1, 0.65 + i * 0.1])
    };
  });
  if (missing) {
    gefs.observed_retrospective = {};
    gefs.precip.surface.mean = [];
    gefs.precip.surface.p50.splice(1, 0, { t: stamp(1.5), v: null });
    delete gefs.soil_moisture['1-2 m'];
  }
  return { init, usgs, flow, gefs };
}

module.exports = { makeDemoData };
