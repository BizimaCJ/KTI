import { ApiError, getRoads, submitReport } from './api.js';
import { clear, el } from './dom.js';
import { setStatus } from './render.js';

const form = document.getElementById('report-form');
const typeEl = document.getElementById('type');
const roadEl = document.getElementById('road');
const descEl = document.getElementById('description');
const nameEl = document.getElementById('name');
const contactEl = document.getElementById('contact');
const countEl = document.getElementById('count');
const statusEl = document.getElementById('form-status');
const submitBtn = document.getElementById('submit');
const confirmation = document.getElementById('confirmation');

async function loadRoads() {
  try {
    const roads = await getRoads();
    clear(roadEl);
    roadEl.append(el('option', { text: 'Choose a road', attrs: { value: '' } }));
    for (const road of roads) roadEl.append(el('option', { text: road.name, attrs: { value: String(road.id) } }));
  } catch (error) {
    clear(roadEl);
    roadEl.append(el('option', { text: 'Roads could not be loaded', attrs: { value: '' } }));
    setStatus(statusEl, error instanceof ApiError ? error.message : 'Could not load the road list.', true);
  }
}

// Checks the same rules as the server so people get quick, clear feedback.
function validate() {
  if (!typeEl.value) return 'Please choose what happened.';
  if (!roadEl.value) return 'Please choose a road.';
  if (descEl.value.trim().length < 10) return 'Please describe what you saw (at least 10 characters).';
  return null;
}

descEl.addEventListener('input', () => { countEl.textContent = `${descEl.value.length} / 500`; });

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const problem = validate();
  if (problem) { setStatus(statusEl, problem, true); return; }
  submitBtn.disabled = true;
  setStatus(statusEl, 'Sending...');
  try {
    const result = await submitReport({
      type: typeEl.value,
      road_id: Number(roadEl.value),
      description: descEl.value,
      reporter_name: nameEl.value,
      reporter_contact: contactEl.value,
    });
    form.hidden = true;
    clear(confirmation);
    confirmation.hidden = false;
    confirmation.append(
      el('h2', { text: `Report received: ${result.reference}` }),
      el('p', { text: result.message }),
      el('p', {}, el('a', { text: 'Back to traffic now', attrs: { href: 'index.html' } })),
    );
  } catch (error) {
    setStatus(statusEl, error instanceof ApiError ? error.message : 'Something went wrong. Please try again.', true);
  } finally {
    submitBtn.disabled = false;
  }
});

loadRoads();
