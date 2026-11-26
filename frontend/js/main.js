import { ApiError, getOverview } from './api.js';
import { renderIncidents, renderRoads, renderSummary, setStatus } from './render.js';
import { formatTime } from './format.js';

const REFRESH_MS = 30000;

const summaryEl = document.getElementById('summary');
const roadsEl = document.getElementById('roads');
const incidentsEl = document.getElementById('incidents');
const statusEl = document.getElementById('status');
const refreshBtn = document.getElementById('refresh');

let controller = null;
let timer = null;

async function load({ manual = false } = {}) {
  if (controller) controller.abort();
  controller = new AbortController();
  refreshBtn.disabled = true;
  if (manual) setStatus(statusEl, 'Refreshing...');
  try {
    const overview = await getOverview({ signal: controller.signal });
    renderSummary(summaryEl, overview);
    renderRoads(roadsEl, overview);
    renderIncidents(incidentsEl, overview);
    setStatus(statusEl, `Checked at ${formatTime(new Date().toISOString())}. Updates automatically every 30 seconds.`);
  } catch (error) {
    if (error.name === 'AbortError') return;
    const message = error instanceof ApiError ? error.message : 'Something went wrong. Please try again.';
    setStatus(statusEl, `${message} Showing the last data we have, if any.`, true);
  } finally {
    refreshBtn.disabled = false;
  }
}

function schedule() {
  clearInterval(timer);
  timer = setInterval(() => { if (!document.hidden) load(); }, REFRESH_MS);
}

refreshBtn.addEventListener('click', () => load({ manual: true }));
document.addEventListener('visibilitychange', () => { if (!document.hidden) load(); });

load();
schedule();
