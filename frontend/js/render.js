import { clear, el } from './dom.js';
import { INCIDENT_TYPES, formatTime, levelInfo, newestTimestamp, timeAgo } from './format.js';

export function renderSummary(container, overview) {
  clear(container);
  container.className = 'summary';
  if (!overview.has_data) {
    container.append(
      el('h2', { text: 'No traffic data yet' }),
      el('p', { text: 'Traffic information is not available at the moment. Please check again shortly.' }),
    );
    return;
  }
  const info = levelInfo(overview.worst_level);
  container.classList.add(`level-${overview.worst_level}`);
  const updated = newestTimestamp(overview.roads);
  container.append(
    el('h2', { text: `Worst conditions right now: ${info.label}` }),
    el('p', { text: `${info.text} Data updated at ${formatTime(updated)} (${timeAgo(updated)}).` }),
  );
}

function roadCard(road) {
  const info = levelInfo(road.level);
  const delayText = road.delay_minutes === 0 ? 'No delay' : `+${road.delay_minutes} min`;
  const meta = el('p', { className: 'meta', text: `Updated ${formatTime(road.recorded_at)}` });
  if (road.is_simulated) meta.append(el('span', { className: 'tag-sim', text: 'Simulated' }));
  return el(
    'article',
    { className: `road-card level-${road.level}` },
    el('h3', { text: road.road_name }),
    el('span', { className: `badge level-${road.level}`, text: info.label }),
    el(
      'div',
      { className: 'metrics' },
      el('div', { className: 'metric' },
        el('div', { className: 'value', text: delayText }),
        el('div', { className: 'label', text: 'Estimated delay' })),
      el('div', { className: 'metric' },
        el('div', { className: 'value', text: `${Math.round(road.average_speed_kmh)} km/h` }),
        el('div', { className: 'label', text: 'Average speed' })),
    ),
    meta,
  );
}

export function renderRoads(container, overview) {
  clear(container);
  if (!overview.roads.length) {
    container.append(el('p', { className: 'empty', text: 'No traffic conditions to show yet.' }));
    return;
  }
  for (const road of overview.roads) container.append(roadCard(road));
}

function incidentItem(incident) {
  const where = incident.intersection_name
    ? `${incident.road_name}, near ${incident.intersection_name}`
    : incident.road_name;
  const meta = el('p', { className: 'meta', text: `Reported ${timeAgo(incident.reported_at)}` });
  if (incident.is_simulated) meta.append(el('span', { className: 'tag-sim', text: 'Simulated' }));
  return el(
    'li',
    { className: 'incident' },
    el('span', { className: 'type', text: INCIDENT_TYPES[incident.type] || 'Incident' }),
    el('span', { text: ` on ${where}` }),
    el('p', { text: incident.description }),
    meta,
  );
}

export function renderIncidents(container, overview) {
  clear(container);
  if (!overview.incidents.length) {
    container.append(el('li', { className: 'empty', text: 'No active incidents reported.' }));
    return;
  }
  for (const incident of overview.incidents) container.append(incidentItem(incident));
}

export function setStatus(node, message, isError = false) {
  node.textContent = message;
  node.classList.toggle('error', isError);
}
