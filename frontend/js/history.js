import { ApiError, getHistory, getRoads } from './api.js';
import { clear, el } from './dom.js';
import { levelInfo } from './format.js';
import { setStatus } from './render.js';

const roadEl = document.getElementById('road');
const hoursEl = document.getElementById('hours');
const statusEl = document.getElementById('history-status');
const tableEl = document.getElementById('history-table');
const bodyEl = document.getElementById('history-body');

const dateTime = new Intl.DateTimeFormat('en-GB', {
  day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: 'Africa/Kigali',
});

function row(reading) {
  const info = levelInfo(reading.level);
  const delay = reading.delay_minutes === 0 ? 'No delay' : `+${reading.delay_minutes} min`;
  return el('tr', {},
    el('td', { text: dateTime.format(new Date(reading.recorded_at)) }),
    el('td', {}, el('span', { className: `badge level-${reading.level}`, text: info.label })),
    el('td', { text: delay }),
    el('td', { text: `${Math.round(reading.average_speed_kmh)} km/h` }),
  );
}

async function load() {
  if (!roadEl.value) return;
  setStatus(statusEl, 'Loading...');
  try {
    const rows = await getHistory(roadEl.value, hoursEl.value);
    clear(bodyEl);
    tableEl.hidden = rows.length === 0;
    if (!rows.length) {
      setStatus(statusEl, 'No history exists for this road in the selected period.');
      return;
    }
    for (const reading of rows) bodyEl.append(row(reading));
    setStatus(statusEl, `${rows.length} readings, newest first. Simulated data.`);
  } catch (error) {
    tableEl.hidden = true;
    setStatus(statusEl, error instanceof ApiError ? error.message : 'Something went wrong. Please try again.', true);
  }
}

async function init() {
  try {
    const roads = await getRoads();
    clear(roadEl);
    for (const road of roads) roadEl.append(el('option', { text: road.name, attrs: { value: String(road.id) } }));
    await load();
  } catch (error) {
    clear(roadEl);
    roadEl.append(el('option', { text: 'Roads could not be loaded', attrs: { value: '' } }));
    setStatus(statusEl, error instanceof ApiError ? error.message : 'Could not load the road list.', true);
  }
}

roadEl.addEventListener('change', load);
hoursEl.addEventListener('change', load);
init();
