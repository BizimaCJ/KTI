export const LEVELS = {
  FREE_FLOW: { label: 'Free flow', text: 'Traffic is moving normally.' },
  MODERATE: { label: 'Moderate', text: 'Traffic is slower than normal.' },
  HEAVY: { label: 'Heavy', text: 'Significant congestion.' },
  BLOCKED: { label: 'Blocked', text: 'Traffic is effectively stopped.' },
};

export const INCIDENT_TYPES = {
  CRASH: 'Crash',
  FLOODING: 'Flooding',
  ROADWORKS: 'Roadworks',
  BLOCKAGE: 'Blockage',
  OTHER: 'Incident',
};

const TIME_ZONE = 'Africa/Kigali';

export function levelInfo(level) {
  return LEVELS[level] || { label: 'Unknown', text: '' };
}

export function formatTime(iso) {
  return new Intl.DateTimeFormat('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: TIME_ZONE })
    .format(new Date(iso));
}

export function timeAgo(iso, now = new Date()) {
  const minutes = Math.max(0, Math.round((now - new Date(iso)) / 60000));
  if (minutes < 1) return 'just now';
  if (minutes === 1) return '1 minute ago';
  if (minutes < 60) return `${minutes} minutes ago`;
  const hours = Math.round(minutes / 60);
  return hours === 1 ? '1 hour ago' : `${hours} hours ago`;
}

export function newestTimestamp(roads) {
  return roads.reduce((latest, r) => (!latest || r.recorded_at > latest ? r.recorded_at : latest), null);
}
