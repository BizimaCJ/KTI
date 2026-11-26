// All network calls live here so the rest of the app never touches fetch().
export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

function messageFrom(body) {
  if (body && typeof body.detail === 'string') return body.detail;
  // FastAPI sends a list of problems for invalid input; show the first one in plain words.
  if (body && Array.isArray(body.detail) && body.detail[0] && body.detail[0].msg) {
    return String(body.detail[0].msg).replace(/^Value error, /, '');
  }
  return null;
}

async function request(path, { signal, method = 'GET', body } = {}) {
  let response;
  try {
    response = await fetch(path, {
      method,
      signal,
      headers: { Accept: 'application/json', ...(body ? { 'Content-Type': 'application/json' } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new ApiError('Cannot reach the server. Check your connection and try again.', 0);
  }
  if (!response.ok) {
    let detail = 'Something went wrong. Please try again.';
    try {
      detail = messageFrom(await response.json()) || detail;
    } catch (_) { /* keep the default message */ }
    throw new ApiError(detail, response.status);
  }
  return response.json();
}

export const getOverview = (options) => request('/api/overview', options);
export const getRoads = () => request('/api/network/roads');
export const getHistory = (roadId, hours) => request(`/api/traffic/history?road_id=${roadId}&hours=${hours}`);
export const submitReport = (report) => request('/api/incidents/report', { method: 'POST', body: report });
